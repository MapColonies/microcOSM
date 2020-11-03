#!/usr/bin/env python3
import os
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

DOWNLOAD_DIR = '/tmp/cache'

os.environ['PGHOST'] = PGHOST
os.environ['PGPORT'] = PGPORT
os.environ['PGUSER'] = PGUSER
os.environ['PGDATABASE'] = PGDATABASE
os.environ['PGPASSWORD'] = PGPASSWORD

divide_for_days = 1000000
divide_for_month = 1000
divide_for_years = 1000

tiler_db_state_file_path = os.path.join(EXPIRED_DIRECTORY, "state.txt")

log = JSONLogger('main-debug', additional_fields={'service': 'osm2pgsql'})


def pg_is_ready():
    ready = False
    log.info('waiting for pg...')
    while not ready:
        res = os.popen(f'pg_isready -h {PGHOST} -p 5432').read()
        if (res.find('accepting connections') > 0):
            ready = True
            log.info('pg is ready for connections')
    return ready


def first_import():
    log.info('starting first osm import')
    os.system("osm2pgsql \
                --create \
                --slim \
                -G \
                --hstore \
                --tag-transform-script /src/openstreetmap-carto.lua \
                -C 2500 \
                --number-processes 4 \
                -S /src/openstreetmap-carto.style \
                /src/first-osm-import.osm"
              )
    log.info('first import is done')


def parse_integer_to_directory_number(integer):
    return "{0:0=3d}".format(integer)


def is_file_or_directory(path):
    return os.path.exists(path)


def get_file_from_replication_server(path):
    url = '/'.join([REPLICATION_URL, path])
    log.info(f"fetching file from {url}")
    result = requests.get(url)
    return (result.ok, result.text)


def download(path: str, dest_folder: str):
    url = '/'.join([REPLICATION_URL, path])

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    # be careful with file names
    filename = url.split('/')[-1].replace(" ", "_")
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        log.info(f"saving file to {os.path.abspath(file_path)}")
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:
        log.error(f'file download failed with error code {r.status_code}')
    return r.status_code


def extract_integer_value(content, find, throw_not_found=True, none_found=-1):
    found = re.findall(f'{find}=.*', content)
    if len(found) == 0:
        if throw_not_found:
            raise LookupError(f'"{find}=" is not present in the state.txt')
        else:
            return none_found

    found = found[0].split('=')[1]
    try:
        found = int(found)
    except ValueError:
        raise ValueError(
            f'"{find}=" must be follow by a positive integer at state.txt')

    return found


def has_data():
    flag = True
    while (flag):
        try:
            conn = psycopg2.connect(
                f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}")
            cur = conn.cursor()
            cur.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            data = cur.fetchone()[0]
            flag = False
            return data
        # should it do this or just crash?
        except:
            time.sleep(UPDATE_INTERVAL)


def update_db_with_replication(api_db_sequence_number, tiler_db_sequence_number):
    for i in range(tiler_db_sequence_number+1, api_db_sequence_number+1):
        dir1 = parse_integer_to_directory_number(int(i / divide_for_days))
        dir2 = parse_integer_to_directory_number(int(i / divide_for_month))
        state = parse_integer_to_directory_number(int(i % divide_for_years))

        # creating the folder to store the expired tiles list if it does not exist
        if not is_file_or_directory('/'.join([EXPIRED_DIRECTORY, dir1])):
            os.mkdir('/'.join([EXPIRED_DIRECTORY, dir1]))

        EXPIRED_PATH = '/'.join([EXPIRED_DIRECTORY, dir1, dir2])
        if not is_file_or_directory(EXPIRED_PATH):
            os.mkdir(EXPIRED_PATH)

        # downloading the osc file
        download('/'.join([dir1, dir2, state + '.osc.gz']), DOWNLOAD_DIR)

        osc = os.path.join(DOWNLOAD_DIR, state + ".osc.gz")

        log.info(
            f'updating replications where api_db sequence={api_db_sequence_number} and tiler_db starting sequence={tiler_db_sequence_number} and current={i}')

        if (not is_file_or_directory(osc)):
            return

        os.system(f"osm2pgsql \
                        --append \
                        --slim \
                        -G \
                        --hstore \
                        --tag-transform-script /src/openstreetmap-carto.lua \
                        -C 2500 \
                        --number-processes 2 \
                        -S /src/openstreetmap-carto.style \
                        {osc} \
                        -e17 \
                        -o {EXPIRED_PATH}/{state}-expire.list"
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
                f"updating state file at {tiler_db_state_file_path} with sequenceNumber={sequence_number}")
            expired_file.truncate(0)
            expired_file.seek(0)
            expired_file.write(str(expired_content))


def get_api_db_sequence():
    (is_ok, api_db_replication_state) = get_file_from_replication_server('state.txt')

    if (not is_ok):
        log.error(
            f"state file not found in remote server {REPLICATION_URL}, sleeping for {UPDATE_INTERVAL}")
        return -1
    try:
        return extract_integer_value(
            api_db_replication_state, "sequenceNumber")
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
                f"sequenceNumber=0\n")
        return 0
    # retrive the sequence number from the file
    else:
        with open(tiler_db_state_file_path, 'r') as fp:
            return extract_integer_value(
                fp.read(), "sequenceNumber")


def update_data_loop():
    log.info('starting replications update loop')
    while True:
        log.info(f"sleeping for {UPDATE_INTERVAL}")
        time.sleep(UPDATE_INTERVAL)

        api_db_sequence_number = get_api_db_sequence()
        # if true than it means the state wasnt found
        if (api_db_sequence_number == -1):
            continue

        tiler_db_sequence_number = get_tiler_db_sequence()

        log.info(
            f"api_db_sequence = {api_db_sequence_number}, tiler_db_sequence={tiler_db_sequence_number}")

        # check if an update is needed
        if (api_db_sequence_number != tiler_db_sequence_number):
            update_db_with_replication(
                api_db_sequence_number, tiler_db_sequence_number)


log.info('osm2pgsql container started')

if pg_is_ready():
    if (has_data() <= 5):
        first_import()
    update_data_loop()
