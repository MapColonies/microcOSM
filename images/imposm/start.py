#!/usr/bin/env python3
import os
import re
import time
import json
import subprocess
import sys
from datetime import datetime

import psycopg2
import requests
from jsonlogger.logger import JSONLogger
from osmeterium.run_command import run_command

state_file = 'state.txt'
pbf_file = 'first-osm-import.pbf'
sql_helpers = 'postgis_helpers.sql'
sql_index = 'postgis_index.sql'

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']
pg_port = os.environ['POSTGRES_PORT']

cache_dir_path = '/mnt/data/cache'
diff_dir_path = '/mnt/data/diff'
expired_tiles_dir_path = os.environ['CONFIG_EXPIRED_TILES_DIR']
replication_url = os.environ['IMPOSM_REPLICATION_URL']
last_state_file = 'last.state.txt'

db_init_table_name = 'goad'

imposm_config = {
    'cachedir': cache_dir_path,
    'diffdir': diff_dir_path,
    'expiretiles_dir': expired_tiles_dir_path,
    'expiretiles_zoom': int(os.environ['CONFIG_EXPIRED_TILES_ZOOM']),
    'connection': 'postgis://{0}:{1}@{2}/{3}'.format(pg_user, pg_password, pg_host, pg_db),
    'mapping': 'imposm3.json',
    'replication_url': replication_url,
    'replication_interval': os.environ['CONFIG_REPLICATION_INTERVAL']
}

log = JSONLogger('main-debug', additional_fields={'service': 'imposm'})


def get_pg_connection():
    return psycopg2.connect(host=pg_host, port=pg_port,
                            dbname=pg_db, user=pg_user, password=pg_password)


def execute_sql_script(script_name):
    conn = get_pg_connection()
    log.info('loading script {0} to the db'.format(script_name))
    cur = conn.cursor()
    cur.execute(open(script_name, "r").read())
    conn.close()


def get_api_db_creation_timestamp():
    url = '{0}000/000/000.state.txt'.format(replication_url)
    log.info('fetching file from {0}'.format(url))
    result = requests.get(url)

    if not result.ok:
        log.error('failed retrieving state file. status code {0}'.format(
            result.status_code))
        sys.exit(1)

    raw_timestamp = re.search("timestamp=(.*)", result.text).group(1)
    return datetime.strptime(raw_timestamp, r'%Y-%m-%dT%H\:%M\:%SZ')


def is_db_initialized():
    log.info('checking if database is initialized')
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT count(*) FROM information_schema.tables WHERE table_name = \'{0}\''.format(db_init_table_name))
    data = cur.fetchone()[0]
    conn.close()
    return data > 0


def mark_db_as_initialized():
    log.info('marking database as initialized')
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE {0} (v BOOLEAN)'.format(db_init_table_name))
    conn.commit()
    conn.close()


def get_command_stdout_iter(process):
    for stdout_line in iter(process.stdout.readline, ''):
        yield stdout_line


def on_command_fail(command_name, exit_code):
    'command {0} has terminated with error code {1}'.format(
        command_name, exit_code)
    sys.exit(1)


def is_last_state_exists():
    return os.path.isfile(os.path.join(diff_dir_path, last_state_file))


def initialize_db():
    # set the pbf file time to match the db creation time
    execute_sql_script(sql_helpers)

    log.info('initializing the db with empty pbf')
    creation_time = time.mktime(get_api_db_creation_timestamp().timetuple())
    os.utime(pbf_file, (creation_time, creation_time))

    init_command = 'imposm import -config config.json -read {0} -write -diff -diffdir {1} -cachedir {2}'.format(
        pbf_file, diff_dir_path, cache_dir_path)
    run_command(init_command, log.info, log.error,
                lambda exit_code: on_command_fail('imposm import', exit_code), lambda: None)

    if not is_last_state_exists():
        log.error(f'{last_state_file} is missing, could not update data')
        sys.exit(1)

    deploy_command = 'imposm import -config config.json -deployproduction'
    run_command(deploy_command, log.info, log.error,
                lambda exit_code: on_command_fail('imposm import deploy', exit_code), lambda: None)
    mark_db_as_initialized()


def update_data():
    run_command('imposm run -config config.json', log.info, log.error,
                lambda exit_code: on_command_fail('imposm run', exit_code), lambda: None)


def main():
    for dir_path in [cache_dir_path, diff_dir_path]:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    if not os.path.exists(expired_tiles_dir_path):
        raise Exception(
            'Folder {0} was not found, please check again'.format(expired_tiles_dir_path))

    with open('config.json', 'w') as fp:
        json.dump(imposm_config, fp)

    if not is_db_initialized():
        initialize_db()
    update_data()


if __name__ == '__main__':
    main()
