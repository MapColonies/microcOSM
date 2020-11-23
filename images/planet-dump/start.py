#!/usr/bin/env python3
import os
# import signal
import sys
import shutil
from datetime import datetime
import time
from croniter import croniter
import pause
from jsonlogger.logger import JSONLogger
from osmeterium.run_command import run_command

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']

dump_cron_pattern = os.environ['CREATE_DUMP_SCHEDULE']
dumps_storage_folder = os.environ.get('DUMP_STORAGE_FOLDER', '/mnt/dump')
dump_file_prefix = os.environ.get('DUMP_FILE_PREFIX', 'dump')


def handle_osmosis_failure(exit_code):
    log.error('osmosis failed with exit code {}'.format(exit_code))
    sys.exit(1)

def get_file_name():
    iso_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    return '{0}-{1}.osm.pbf'.format(dump_file_prefix, iso_time)


def create_dump():
    file_name = get_file_name()
    create_dump_command = 'osmosis --read-apidb host={0} database={1} user={2} password={3} validateSchemaVersion=no --write-pbf file={4}'.format(pg_host, pg_db, pg_user, pg_password, file_name)
    
    log.info('creating dump')
    start_time = time.perf_counter()

    run_command(create_dump_command, log.info, log.error, handle_osmosis_failure, lambda: None)

    end_time = time.perf_counter()

    run_time = end_time - start_time
    log.info('dump {0} as been created succesfuly, it took {1:0.4f} seconds'.format(file_name, run_time))

    shutil.move('/app/{}'.format(file_name), os.path.join(dumps_storage_folder, file_name))

def main():
    iter = croniter(expr_format=dump_cron_pattern, start_time=datetime.now())
    while True:
        execute_time = iter.get_next(datetime)
        log.info('paused until {}'.format(
            execute_time.strftime('%d/%m/%Y %H:%M:%S')))
        pause.until(execute_time)
        create_dump()

if __name__ == '__main__':
    os.makedirs('/var/log/osm-seed', exist_ok=True)
    log = JSONLogger(
      'main-debug', additional_fields={'service': 'planet-dumper'})

    main()