#!/usr/bin/env python3
import os
import psycopg2
import re
import time
from jsonlogger.logger import JSONLogger

PGHOST = os.environ['POSTGRES_HOST']
PGPORT = os.environ['POSTGRES_PORT']
PGUSER = os.environ['POSTGRES_USER']
PGDATABASE = os.environ['POSTGRES_DB']
PGPASSWORD = os.environ['POSTGRES_PASSWORD']

os.environ['PGHOST'] = PGHOST
os.environ['PGPORT'] = PGPORT
os.environ['PGUSER'] = PGUSER
os.environ['PGDATABASE'] = PGDATABASE
os.environ['PGPASSWORD'] = PGPASSWORD

replication_directory = os.environ['REPLICATION_DIR']
expired_directory = os.environ['EXPIRED_DIR']

update_interval = int(os.environ['OSM2PGSQL_UPDATE_INTERVAL'])

divide_for_days = 1000000
divide_for_month = 1000
divide_for_years = 1000

log = JSONLogger('main-debug', additional_fields={'service': 'osm2pgsql'})


def parse_integer_to_directory_number(integer):
    return "{0:0=3d}".format(integer)


def is_file_or_directory(path):
    return os.path.exists(path)


def pg_is_ready():
    ready = False
    log.info('waiting for pg...')
    while not ready:
        res = os.popen(f'pg_isready -h {PGHOST} -p 5432').read()
        if (res.find('accepting connections') > 0):
            ready = True
            log.info('pg is ready for connections')
    return ready


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
            time.sleep(update_interval)


def update_db_with_replication(sequence_number, last_append):
    for i in range(last_append+1, sequence_number):
        dir1 = parse_integer_to_directory_number(int(i / divide_for_days))
        dir2 = parse_integer_to_directory_number(int(i / divide_for_month))
        state = parse_integer_to_directory_number(int(i % divide_for_years))

        dir_path = os.path.join(expired_directory, dir1, dir2)

        if (not is_file_or_directory(dir_path)):
            os.makedirs(dir_path)

        osc = os.path.join(replication_directory, dir1,
                           dir2, state + ".osc.gz")

        log.info(
            f'updating replications where sequence_number={sequence_number} and last_append={last_append} and current={i}')

        if (is_file_or_directory(osc)):
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
                        -o {expired_directory}/{dir1}/{dir2}/{state}-expire.list"
                      )


def update_state_file(expired_state_file_path, sequence_number, last_append):
    with open(expired_state_file_path, 'r+') as expired_file:
        expired_content = expired_file.read()

        sequence_numberFound = re.search('sequenceNumber=.*', expired_content)
        last_appendFound = re.search('lastAppend=.*', expired_content)
        if sequence_numberFound:
            re.sub(r'(?<=sequence_number=)\d+', str(sequence_number),
                   expired_content, 1)  # update sequenceNumber value

        if last_appendFound:
            re.sub(r'(?<=last_append=)\d+', str(last_append),
                   expired_content, 1)  # update lastAppend value

        expired_file.truncate(0)
        expired_file.seek(0)
        expired_file.write(str(expired_content))


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


def update_tiles(sequence_number, last_append):
    expired_state_file_path = os.path.join(expired_directory, "state.txt")

    if (not is_file_or_directory(expired_state_file_path)):
        log.info('creating osm2pgsql state file as one does not exist')
        with open(expired_state_file_path, 'w+') as fp:
            fp.write(
                f"sequence_number={sequence_number}\nlast_append={last_append}\n")

    update_db_with_replication(sequence_number, last_append)
    update_state_file(expired_state_file_path, sequence_number, last_append)


def update_data_loop():
    log.info('starting replications update loop')
    last_append = -1
    while True:
        replication_state_file_path = f"{replication_directory}/state.txt"

        if (not is_file_or_directory(replication_state_file_path)):
            log.info(f"state file not found, sleeping for {update_interval}")
            time.sleep(update_interval)
            continue

        replication_state_file = open(replication_state_file_path)
        replication_state_file_content = replication_state_file.read()

        try:
            sequence_number = extract_integer_value(
                replication_state_file_content, "sequenceNumber")
        except:
            log.error('sequence_number must be a positive integer at state.txt')
            raise
        # try:
        #     last_append = extract_integer_value(
        #         replication_state_file_content, "lastAppend")
        # except:
        #     last_append = -1

        replication_state_file.close()

        if (sequence_number != last_append):
            update_tiles(sequence_number, last_append)
        last_append += 1


log.info('osm2pgsql container started')

if pg_is_ready():
    if (has_data() <= 5):
        first_import()
    update_data_loop()
