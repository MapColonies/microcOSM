#!/usr/bin/env python3
import os
import sys
import shutil
from datetime import datetime
import time
from croniter import croniter
import pause

from MapColoniesJSONLogger.logger import generate_logger
from osmeterium.run_command import run_command

base_log_path = '/var/log'
app_name = 'planet-dump-service'

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']

dump_cron_pattern = os.environ['CREATE_DUMP_SCHEDULE_CRON']
dumps_storage_folder = os.environ.get('DUMP_STORAGE_FOLDER', '/mnt/dump')
dump_file_prefix = os.environ.get('DUMP_FILE_PREFIX', 'dump')
osmosis_omit_metadata = os.environ.get('OSMOSIS_OMIT_METADATA', 'true')

log = None
process_log = None
app_name = 'planet-dump'
osmosis = 'osmosis'

def handle_osmosis_failure(exit_code):
    log.error('osmosis failed with exit code {}'.format(exit_code))
    sys.exit(1)


def get_dump_file_name():
    iso_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    return '{0}-{1}.osm.pbf'.format(dump_file_prefix, iso_time)


def create_dump():
    file_name = get_dump_file_name()
    create_dump_command = 'osmosis --read-apidb host={0} database={1} user={2} password={3} validateSchemaVersion=no --write-pbf omitmetadata={4} file={5}'.format(
        pg_host, pg_db, pg_user, pg_password, osmosis_omit_metadata, file_name)

    log.info('creating dump')
    start_time = time.perf_counter()

    run_command(create_dump_command, process_log.info,
                process_log.info, handle_osmosis_failure, lambda: None)

    end_time = time.perf_counter()

    run_time = end_time - start_time
    log.info('dump {0} as been created successfully, it took {1:0.4f} seconds'.format(
        file_name, run_time))

    shutil.move(file_name, os.path.join(dumps_storage_folder, file_name))


def main():
    iter = croniter(expr_format=dump_cron_pattern, start_time=datetime.now())
    while True:
        execute_time = iter.get_next(datetime)
        log.info('paused until {}'.format(
            execute_time.strftime('%d/%m/%Y %H:%M:%S')))
        pause.until(execute_time)
        create_dump()


if __name__ == '__main__':
    logs_folder = os.path.join(base_log_path, app_name)
    os.makedirs(logs_folder, exist_ok=True)

    log_file_extention = '.log'
    base_log_path = os.path.join('/var/log', app_name)
    service_logs_path = os.path.join(base_log_path, app_name + log_file_extention)
    mod_tile_log_path = os.path.join(base_log_path, osmosis + log_file_extention)
    os.makedirs(base_log_path, exist_ok=True)
    log = generate_logger(app_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': service_logs_path},{ 'type': 'stream', 'output': 'stderr' }])
    process_log = generate_logger(osmosis, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': mod_tile_log_path}, { 'type': 'stream', 'output': 'stderr' }])
    log.info('planet dump container started')
    main()
