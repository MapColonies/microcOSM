#!/usr/bin/env python3
import time
from datetime import datetime
import signal
import os
import glob
import sys

from MapColoniesJSONLogger.logger import generate_logger
from osmeterium.run_command import run_command, run_command_async

EXPIRE_TILES_DIR = os.environ.get('EXPIRE_TILES_DIR', '/mnt/expiretiles')
CONFIG_PATH = '/opt/tegola_config/config.toml'
EXPIRE_TILES_LIST_FILE = 'expire_tiles.txt'
MAX_ZOOM = os.environ['TILER_CACHE_MAX_ZOOM']
MIN_ZOOM = os.environ['TILER_CACHE_MIN_ZOOM']
INTERVAL = os.environ['TILER_CACHE_UPDATE_INTERVAL']
os.environ["PATH"] = os.environ.get("PATH") + ':/opt'

app_name = 'tegola'
log = None
process_log = None


def purgeExpireTiles():
    with open(EXPIRE_TILES_LIST_FILE, 'w') as writer:
        for filepath in glob.iglob(f'{EXPIRE_TILES_DIR}/**/*.tiles', recursive=True):
            with open(filepath, 'r') as reader:
                tiles = reader.readlines()
                for tile in tiles:
                    writer.write(tile)
            os.remove(filepath)
    if os.path.getsize(EXPIRE_TILES_LIST_FILE) != 0:  # if file is not empty
        log.info('Removing expired tiles from cache')
        tegola_cache_command = 'tegola cache purge tile-list {0} --min-zoom={1} --max-zoom={2} --config={3}'.format(
            EXPIRE_TILES_LIST_FILE, MIN_ZOOM, MAX_ZOOM, CONFIG_PATH)
        run_command(tegola_cache_command, process_log.info, process_log.info,
                    terminate_on_tegola_exit, lambda: None)


def terminate_on_tegola_exit(exit_code=0):
    log.error('tegola terminated with error code {}'.format(exit_code))
    os.kill(os.getpid(), signal.SIGINT)


def main():
    log.info("Starting tiles server!")
    tegola_serve_command = 'tegola serve --config={0}'.format(CONFIG_PATH)

    _ = run_command_async(
        tegola_serve_command, process_log.info, process_log.info, terminate_on_tegola_exit, terminate_on_tegola_exit)

    while True:
        log.info('Updating tiles cache')
        purgeExpireTiles()
        time.sleep(int(INTERVAL))


if __name__ == '__main__':
    tegola_server_name = 'tegola_server'
    base_log_path = os.path.join('/var/log', app_name)
    service_logs_path = os.path.join(base_log_path, app_name + '.log')
    tegola_server_logs_path = os.path.join(base_log_path, tegola_server_name + '.log')
    os.makedirs(base_log_path, exist_ok=True)
    log = generate_logger(app_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': service_logs_path},{ 'type': 'stream', 'output': 'stderr' }])
    process_log = generate_logger(tegola_server_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': tegola_server_logs_path}, { 'type': 'stream', 'output': 'stderr' }])
    main()
