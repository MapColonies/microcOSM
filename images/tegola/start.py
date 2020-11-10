#!/usr/bin/env python3
import time, os, glob
from jsonlogger.logger import JSONLogger

EXPIRE_TILES_DIR = os.environ.get('EXPIRE_TILES_DIR', '/mnt/expiretiles')
CONFIG_PATH = '/opt/tegola_config/config.toml'
EXPIRE_TILES_LIST_FILE = 'expire_tiles.txt'
HOST = os.environ['POSTGRES_HOST']
INTERVAL = os.environ['TILER_CACHE_UPDATE_INTERVAL']
os.environ["PATH"] = os.environ.get("PATH") + ":/opt"

def purgeExpireTiles():
    with open(EXPIRE_TILES_LIST_FILE, 'w') as writer:
        for filepath in glob.iglob(f'{EXPIRE_TILES_DIR}/**/*.tiles', recursive=True):
            with open(filepath, 'r') as reader:
                tiles = reader.readlines()
                for tile in tiles:
                    writer.write(tile)
            os.remove(filepath)
    if os.path.getsize(EXPIRE_TILES_LIST_FILE) != 0: #if file is not empty
        log.info("Remove expire tiles from cache...")
        os.system(f'tegola cache purge tile-list {EXPIRE_TILES_LIST_FILE} --min-zoom=14 --max-zoom=20 --config={CONFIG_PATH}')

def pg_is_ready():
    ready = False
    while not ready:
        res = os.popen(f'pg_isready -h {HOST} -p 5432').read()
        if (res.find('accepting connections') > 0):
            ready = True
    return ready

def main(): 
    log.info("Sleep for a while!")
    time.sleep(100)
    log.info("Starting tiles server!")
    flag = True
    while flag:
        log.info("trying to connect to host")
        if pg_is_ready():
            flag = False
            os.system(f'tegola serve --config={CONFIG_PATH} &')
    
    while True:
        log.info("Updating cache...")
        purgeExpireTiles()
        time.sleep(int(INTERVAL))

if __name__ == '__main__':
    log = JSONLogger('main-debug', additional_fields={'service': 'tegola'})
    main()
