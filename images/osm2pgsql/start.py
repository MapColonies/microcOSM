#!/usr/bin/env python3
import os
import subprocess
import sys
import psycopg2
import re
import time
import requests
from jsonlogger.logger import JSONLogger

# postgres variables
PGHOST = os.environ['POSTGRES_HOST']
PGPORT = os.environ['POSTGRES_PORT']
PGUSER = os.environ['POSTGRES_USER']
PGDATABASE = os.environ['POSTGRES_DB']
PGPASSWORD = os.environ['POSTGRES_PASSWORD']

REPLICATION_URL = os.environ['REPLICATION_URL']
EXPIRED_DIRECTORY = os.environ['EXPIRED_DIR']
UPDATE_INTERVAL = int(os.environ['OSM2PGSQL_UPDATE_INTERVAL'])
PG_CONNECTION_STRING = f'host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}'
READY_TABLE_NAME = 'goad'

DOWNLOAD_DIR = '/tmp/cache'
OSC_FILE_EXTENSION = '.osc.gz'

os.environ['PGHOST'] = PGHOST
os.environ['PGPORT'] = PGPORT
os.environ['PGUSER'] = PGUSER
os.environ['PGDATABASE'] = PGDATABASE
os.environ['PGPASSWORD'] = PGPASSWORD

divide_for_days = 1000000
divide_for_month = 1000
divide_for_years = 1000

tiler_db_state_file_path = os.path.join(EXPIRED_DIRECTORY, 'state.txt')

log = JSONLogger(
    'main-debug', additional_fields={'service': 'osm2pgsql', 'description': 'main log'})
process_log = JSONLogger('main-debug', config={'handlers': {
    'file': {'filename': '/var/log/osm-seed/process.log'}}}, additional_fields={'service': 'osm2pgsql', 'description': 'process logs'})


def get_command_stdout_iter(process):
    for stdout_line in iter(process.stdout.readline, ''):
        yield stdout_line


def run_osm2pgsql_command(*argv):
    process = subprocess.Popen(' '.join(('osm2pgsql',) + argv),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               shell=True)
    for stdout_line in get_command_stdout_iter(process):
        if stdout_line:
            process_log.info(stdout_line.strip())
    process.stdout.close()
    return_code = process.wait()

    if (return_code != 0):
        log.error(
            'osm2pgsql command failed with error code {0}'.format(return_code))
        sys.exit(1)


def db_init():
    log.info('starting first osm import')
    run_osm2pgsql_command(
        '--create',
        '--slim',
        '-G',
        '--hstore',
        '--tag-transform-script', '/src/openstreetmap-carto.lua',
        '-C', '2500',
        '--number-processes', '2',
        '-S', '/src/openstreetmap-carto.style',
        '/src/first-osm-import.osm'
    )
    log.info('first import is done')


def parse_integer_to_directory_number(integer):
    return '{0:0=3d}'.format(integer)


def is_file_or_directory(path):
    return os.path.exists(path)


def get_file_from_replication_server(path):
    url = '{0}/{1}'.format(REPLICATION_URL, path)
    log.info(f'fetching file from {url}')
    result = requests.get(url)
    return (result.ok, result.text)


def download(path: str, dest_folder: str):
    url = '{0}/{1}'.format(REPLICATION_URL, path)

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    # be careful with file names
    filename = url.split('/')[-1].replace(' ', '_')
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        log.info(f'saving file to {os.path.abspath(file_path)}')
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)

    else:
        log.error(
            f'file download failed from {url} with error code {r.status_code}')
    return (r.status_code, file_path)


def extract_integer_value(content, find, throw_not_found=True, none_found=-1):
    found = re.findall(f'{find}=.*', content)
    if len(found) == 0:
        if throw_not_found:
            raise LookupError(f'\'{find}=\' is not present in the state.txt')
        else:
            return none_found

    found = found[0].split('=')[1]
    try:
        found = int(found)
    except ValueError:
        raise ValueError(
            f'\'{find}=\' must be follow by a positive integer at state.txt')

    return found


def is_db_initialized():
    flag = True
    while (flag):
        conn = psycopg2.connect(
            PG_CONNECTION_STRING)
        cur = conn.cursor()
        cur.execute(
            f'SELECT count (*) from information_schema.tables where table_name=\'{READY_TABLE_NAME}\'')
        data = cur.fetchone()[0]
        flag = False
        return data > 0


def flag_db_as_initialized():
    # flag = True
    # while (flag):
    log.info('marking database as initialized')
    conn = psycopg2.connect(
        PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute(
        f'CREATE TABLE {READY_TABLE_NAME} (v BOOLEAN)')
    conn.close()
    # flag = False


def update_db_with_replication(api_db_sequence_number, tiler_db_sequence_number):
    for i in range(tiler_db_sequence_number + 1, api_db_sequence_number + 1):
        dir1 = parse_integer_to_directory_number(int(i / divide_for_days))
        dir2 = parse_integer_to_directory_number(int(i / divide_for_month))
        state = parse_integer_to_directory_number(int(i % divide_for_years))

        # creating the folder to store the expired tiles list if it does not exist
        if not is_file_or_directory('/'.join([EXPIRED_DIRECTORY, dir1])):
            os.mkdir('{0}/{1}'.format(EXPIRED_DIRECTORY, dir1))

        EXPIRED_PATH = '{0}/{1}/{2}'.format(EXPIRED_DIRECTORY, dir1, dir2)
        if not is_file_or_directory(EXPIRED_PATH):
            os.mkdir(EXPIRED_PATH)

        # downloading the osc file
        (status_code, osc) = download(
            '{0}/{1}/{2}'.format(dir1, dir2, state + OSC_FILE_EXTENSION), DOWNLOAD_DIR)

        # terminate on failed download or not saving properly
        if status_code >= 400 or not is_file_or_directory(osc):
            sys.exit(1)

        log.info(
            f'updating replications where api_db sequence={api_db_sequence_number} and tiler_db starting sequence={tiler_db_sequence_number} and current={i}')

        run_osm2pgsql_command(
            '--append',
            '--slim',
            '-G',
            '--hstore',
            '--tag-transform-script', '/src/openstreetmap-carto.lua',
            '-C', '2500',
            '--number-processes', '2',
            '-S', '/src/openstreetmap-carto.style',
            osc,
            '-e17',
            '-o', '{0}/{1}-expire.list'.format(EXPIRED_PATH, state)
        )
        update_state_file(i)

        # cleanup of the state file that was applied
        os.remove(osc)


def update_state_file(sequence_number):
    with open(tiler_db_state_file_path, 'r+') as expired_file:
        expired_content = expired_file.read()

        sequence_numberFound = re.search('sequenceNumber=.*', expired_content)

        if sequence_numberFound:
            expired_content = re.sub(r'(?<=sequenceNumber=)\d+', str(sequence_number),
                                     expired_content, 1)  # update sequenceNumber value
            log.info(
                f'updating state file at {tiler_db_state_file_path} with sequenceNumber={sequence_number}')
            expired_file.truncate(0)
            expired_file.seek(0)
            expired_file.write(str(expired_content))


def get_api_db_sequence():
    (is_ok, api_db_replication_state) = get_file_from_replication_server('state.txt')

    if (not is_ok):
        log.error(
            f'state file not found in remote server {REPLICATION_URL}, sleeping for {UPDATE_INTERVAL}')
        return -1
    try:
        return extract_integer_value(
            api_db_replication_state, 'sequenceNumber')
    except:
        log.error(
            'api_db_sequence_number must be a positive integer at state.txt')
        raise


def get_tiler_db_sequence():
    # create the state file as start from 0 as it was not found
    if (not is_file_or_directory(tiler_db_state_file_path)):
        log.info('creating osm2pgsql state file as one does not exist')
        with open(tiler_db_state_file_path, 'w+') as fp:
            fp.write(
                f'sequenceNumber=0\n')
        return 0
    # retrive the sequence number from the file
    else:
        with open(tiler_db_state_file_path, 'r') as fp:
            return extract_integer_value(
                fp.read(), 'sequenceNumber')


def update_data_loop():
    log.info('starting replications update loop')
    while True:
        log.info(f'sleeping for {UPDATE_INTERVAL}')
        time.sleep(UPDATE_INTERVAL)

        api_db_sequence_number = get_api_db_sequence()
        # if true than it means the state wasnt found
        if (api_db_sequence_number == -1):
            continue

        tiler_db_sequence_number = get_tiler_db_sequence()

        log.info(
            f'api_db_sequence = {api_db_sequence_number}, tiler_db_sequence={tiler_db_sequence_number}')

        # check if an update is needed
        if (api_db_sequence_number != tiler_db_sequence_number):
            update_db_with_replication(
                api_db_sequence_number, tiler_db_sequence_number)


def main():
    log.info('osm2pgsql container started')
    # if pg_is_ready():
    if not is_db_initialized():
        db_init()
        flag_db_as_initialized()
    update_data_loop()


if __name__ == '__main__':
    main()
