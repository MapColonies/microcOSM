import os, re, time, json, subprocess, sys
from queue import Queue, Empty
from threading  import Thread

import typing

import psycopg2
from jsonlogger.logger import JSONLogger

state_file = 'state.txt'

pg_user = os.environ['POSTGRES_USER']
pg_password = os.environ['POSTGRES_PASSWORD']
pg_host = os.environ['POSTGRES_HOST']
pg_db = os.environ['POSTGRES_DB']
pg_port = os.environ['POSTGRES_PORT']

cache_dir_path = os.environ['CONFIG_CACHE_DIR']
diff_dir_path = os.environ['CONFIG_DIFF_DIR']
expired_tiles_dir_path = os.environ['CONFIG_EXPIRED_TILES_DIR']

imposm_config: dict = {
    'cachedir': cache_dir_path,
    'diffdir': diff_dir_path,
    'expiretiles_dir': expired_tiles_dir_path,
    'expiretiles_zoom': os.environ['CONFIG_EXPIRED_TILES_ZOOM'],
    'connection': 'postgis://{0}:{1}@{2}/{3}'.format(pg_user, pg_password, pg_host, pg_db),
    'mapping': 'imposm3.json',
    'replication_url': os.environ['CONFIG_REPLICATION_URL'],
    'replication_interval': os.environ['CONFIG_REPLICATION_INTERVAL']
}

log = JSONLogger('main-debug', additional_fields={ 'service': 'imposm' })

def pg_is_ready():
    ready = False
    log.info('waiting for pg...')
    while not ready:
        res = os.popen('pg_isready -h {0} -p 5432'.format(pg_host)).read()
        if (res.find('accepting connections') > 0):
            ready = True
            log.info('pg is ready for connections')
    return ready

def count_tables():
    conn = psycopg2.connect('host={0} port={1} dbname={2} user={3} password={4}'.format(pg_host, pg_port, pg_db, pg_user, pg_password))
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM information_schema.tables WHERE table_schema = \'public\'')
    data = cur.fetchone()[0]
    return data

def update_data_loop():
    process = subprocess.Popen(['imposm', 'run', '-config config.json'], 
                        stdout=subprocess.PIPE,
                        universal_newlines=True)
    while True:
        output = process.stdout.readline()
        log.info(output.strip())
        # Do something else
        return_code = process.poll()
        if return_code is None:
            continue
        log.error('imposm has exited with return code {0}'.format(return_code))
        # Process has finished, read rest of the output 
        for output in process.stdout.readlines():
            log.error(output.strip())
        sys.exit(1)


def main():
    for dir_path in [cache_dir_path, diff_dir_path, expired_tiles_dir_path]:
        if not os.path.exists(dir_path):
            raise Exception('Folder {0} was not found, please check again'.format(dir_path))

    with open('config.json', 'w') as fp:
        json.dump(imposm_config, fp)

    if pg_is_ready():
        update_data_loop()

if __name__ == '__main__':
    main()
