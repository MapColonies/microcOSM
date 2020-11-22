#!/usr/bin/env python3
import os
import signal
import sys
from datetime import datetime
from croniter import croniter
import pause
from jsonlogger.logger import JSONLogger
from osmeterium.run_command import run_command

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']
pg_port = os.environ.get('POSTGRES_PORT', default=5432)

skip_load_on_startup = os.environ.get('SKIP_LOAD_ON_STARTUP', 'False')
cron_expression = os.environ['LOAD_EXTERNAL_SCHEDULE_CRON']
config_file = os.environ.get('CONFIG_FILE_PATH', default='external-data.yaml')

log = JSONLogger(
    'main-debug', additional_fields={'service': 'earth-tiles-loader'})


def on_command_error(exit_code):
    log.error('get-external-data script failed with exit code {}'.format(exit_code))
    os.kill(os.getpid(), signal.SIGINT)


def load_data():
    command = 'PGPASSWORD={0} get-external-data.py -H {1} -d {2} -p {3} -U {4} -c {5}'.format(
        pg_password, pg_host, pg_db, pg_port, pg_user, config_file)
    log.info('starting to load the data')
    run_command(command, log.info, log.error, on_command_error, lambda: None)
    log.info('loading completed')


def main():
    # check if script should load data on startup
    if not skip_load_on_startup.lower() == 'true': 
        load_data()

    iter = croniter(expr_format=cron_expression, start_time=datetime.now())
    while True:
        execute_time = iter.get_next(datetime)
        log.info('paused until {}'.format(
            execute_time.strftime("%d/%m/%Y %H:%M:%S")))
        pause.until(execute_time)
        load_data()


if __name__ == '__main__':
    main()
