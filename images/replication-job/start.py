#!/usr/bin/env python3
import os
from time import sleep

from osmeterium.run_command import run_command
from MapColoniesJSONLogger.logger import generate_logger

app_name = 'replication-job'
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']
pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
replication_directory = os.environ['REPLICATION_DIRECTORY']
osmosis_min_interval = 60000
osmosis_iterations = 0
osmosis_validate_schema_version = False

log = None
process_log = None

def handle_osmosis_failure(exit_code):
    log.error('osmosis has failed with exit code = {0}'.format(exit_code))
    exit(exit_code)

def handle_osmosis_success():
    log.info('osmosis successfully created a replication')

# osmosis tuning: https://wiki.openstreetmap.org/wiki/Osmosis/Tuning,https://lists.openstreetmap.org/pipermail/talk/2012-October/064771.html
def build_osmosis_command(min_interval, iterations, validate_schema_version):
    validate_schema_version = 'yes' if validate_schema_version else 'no'
    return 'osmosis --replicate-apidb iterations={0} minInterval={1} host={2} database={3} user={4} password={5} validateSchemaVersion={6} --write-replication workingDirectory={7}'\
        .format(iterations, min_interval, pg_host, pg_db, pg_user, pg_password, validate_schema_version, replication_directory)

def run_minute_replication():
    osmosis_command = build_osmosis_command(osmosis_min_interval, osmosis_iterations, osmosis_validate_schema_version)
    run_command(osmosis_command, process_log.info, process_log.info, handle_osmosis_failure, handle_osmosis_success)

def main():
    log.info('{0} is up'.format(app_name))
    run_minute_replication()

if __name__ == "__main__":
    osmosis_name = 'osmosis'
    base_log_path = os.path.join('/var/log', app_name)
    service_logs_path = os.path.join(base_log_path, app_name + '.log')
    osmosis_logs_path = os.path.join(base_log_path, osmosis_name + '.log')
    os.makedirs(base_log_path, exist_ok=True)
    log = generate_logger(app_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': service_logs_path},{ 'type': 'stream', 'output': 'stderr' }])
    process_log = generate_logger(osmosis_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': osmosis_logs_path}, { 'type': 'stream', 'output': 'stderr' }])
    main()
