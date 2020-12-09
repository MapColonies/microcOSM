import psycopg2
import re
import subprocess
import sys
import time
from os import path, linesep, environ, mkdir, makedirs

from MapColoniesJSONLogger.logger import generate_logger
from osmeterium.run_command import run_command_async, run_command

SEQUENCE_PATH_DENOMINATORS = [1000000, 1000, 1]
CARTO_FILE = '/src/openstreetmap-carto/project.mml'

EXPIRED_DIRECTORY = environ.get('EXPIRED_DIRECTORY', '/mnt/expired')
RENDER_EXPIRED_TILES_INTERVAL = float(environ.get('RENDER_EXPIRED_TILES_INTERVAL', 60))
TILE_EXPIRE_MIN_ZOOM = int(environ.get('TILE_EXPIRE_MIN_ZOOM', 14))

db_config = {
  'osm_db_name':environ['OSM_POSTGRES_DB'],
  'osm_host':environ['OSM_POSTGRES_HOST'],
  'osm_password':environ['OSM_POSTGRES_PASSWORD'],
  'osm_user':environ['OSM_POSTGRES_USER'],
  'et_db_name':environ['EARTH_TILES_POSTGRES_DB'],
  'et_host':environ['EARTH_TILES_POSTGRES_HOST'],
  'et_password':environ['EARTH_TILES_POSTGRES_PASSWORD'],
  'et_user':environ['EARTH_TILES_POSTGRES_USER']
}
app_name = 'mod-tile'
log = None
process_log = None

def cast_string_to_int(value):
    try:
        return int(value)
    except ValueError:
        return None

# positive thinking
# simplify function
def extract_positive_integer_value(text, key):
    """
    Extract an integer value for a given key in a text
    Args:
        text (str): text to extract value from
        key (str): key to extract value for
    Raises:
        ValueError: value is not a positive integer
    Returns:
        int: extraced value
    """
    found = re.search(fr'{key}=\d+', text)
    if not found:
        return None

    value = found.group(0).split('=')[1]
    integer_value = cast_string_to_int(value)
    if (value is None or integer_value < 0):
        raise ValueError('"{}=" must be followed by a positive integer in text'.format(key)) 
    return integer_value


def get_path_part_from_sequence_number(sequence_number, denominator):
    """
    Get a path part of a sequence number styled path (e.g. 000/002/345)
    Args:
        sequence_number (int): sequence number (a positive integer)
        denominator (int): denominator used to extract the relevant part of a path
    Returns:
        str: part of a path
    """
    return '{:03d}'.format(int(sequence_number / denominator))[-3:]


def unique_tiles_from_files(start, end, directory):
    """
    Ectracts a unique and ordered list of z/x/y expired tiles (e.g. 0/0/0) from files, in a structured replication dir
    Args:
        start (int): index of the first replication file
        end (int): index of the last replication file
        directory (str): path to a directory that contains replication structured dirs with expired tiles lists
    Returns:
        list: unique and ordered list of tiles
    """
    expired_tiles = []
    i = start

    # replication directory structure 004/215/801 corresponds to sequence number 4,215,801
    while i <= end:
        path_parts = [directory]
        path_parts += [get_path_part_from_sequence_number(
            i, denominator) for denominator in SEQUENCE_PATH_DENOMINATORS]
        path_parts[-1] += '-expire.list'
        expired_tiles_file_path = path.sep.join(path_parts)

        try:
            with open(expired_tiles_file_path, 'r') as expired_tiles_file:
                expired_tiles += expired_tiles_file.read().splitlines()
        except FileNotFoundError:
            log.warn(
                f'file {expired_tiles_file_path} not found for sequence number {i}')
        finally:
            i += 1

    expired_tiles = list(set(expired_tiles))
    expired_tiles.sort()
    return expired_tiles


def update_currently_expired_tiles_file(currently_expired_tiles_file_path, expired_tiles):
    """
    Updates the currently expired list of tiles file
    Args:
        currently_expired_tiles_file_path (str): path to the currently expired list of tiles file
        expired_tiles (list): list if of tiles to expire
    """
    # write the expired tiles list to a file
    with open(currently_expired_tiles_file_path, 'w') as currently_expired_file:
        if expired_tiles:
            currently_expired_file.write(linesep.join(expired_tiles))


def update_rendered_state_file(rendered_state_file_path, sequence_number):
    """
    Updates the rendered state file with an updated state (after tile expiration)
    Args:
        rendered_state_file_path (str): path to the state file
        sequence_number (int): current sequence number to update rendered state file with
    """
    with open(rendered_state_file_path, 'r+') as rendered_file:
        rendered_file.write(f'lastRendered={sequence_number}')

def get_sequence_number_from_file(file_path, key):
    try:
        with open(file_path, 'r') as state_file:
            return extract_positive_integer_value(state_file.read(), key)
    except FileNotFoundError as e:
        log.error(f'{e.strerror}: {e.filename}')
        raise e

def get_osm2pgsql_sequence_number(file_path):
    sequence_number = get_sequence_number_from_file(file_path,'sequenceNumber')
    if not sequence_number:
        raise LookupError(f'"sequenceNumber=" is not present in file')
    return sequence_number

def get_rendered_sequence_number(file_path):
    if not path.exists(file_path):
        log.info('initializing rendering state file')
        # with open(file_path, 'w') as rendered_file:
        #     rendered_file.write('lastRendered=1')
        rendered_file = open(file_path, 'w')
        rendered_file.write('lastRendered=1')
        rendered_file.close()
        return 1
    return get_sequence_number_from_file(file_path, 'lastRendered')


def expire_tiles(state_file_path, currently_expired_tiles_file_path, rendered_state_file_path):
    """
    Call mod_tile's render_expired with tiles that need to be re-rendered
    Args:
        state_file_path (str): path to a state file that holds the current replication state defined by the sequence number
        currently_expired_tiles_file_path (str): path to currentlyExpired.list file that holds a list of tiles to be re-rendered
        rendered_state_file_path (str): path to a file that holds the current rendered state relative to sequence number
    """
    # Infinite loop that sleeps between tiles expirations
    while True:
        start = get_rendered_sequence_number(rendered_state_file_path)
        end = get_osm2pgsql_sequence_number(state_file_path)
        if start <= end:
            expired_tiles = unique_tiles_from_files(start, end, EXPIRED_DIRECTORY)
            update_currently_expired_tiles_file(currently_expired_tiles_file_path, expired_tiles)
            if len(expired_tiles) > 0:
                render_expired(currently_expired_tiles_file_path)
                log.info('marked expired tiles for rerendering', extra={'mod_tile_sequence': start, 'osm2pgsql_sequence': end})
            else:
                log.info('no tiles were expired in this interval', extra={'mod_tile_sequence': start, 'osm2pgsql_sequence': end})
            update_rendered_state_file(rendered_state_file_path, end)
    
        time.sleep(RENDER_EXPIRED_TILES_INTERVAL)


def render_expired(currently_expired_tiles_file_path):
    """
    Render expired tiles
    Args:
        currently_expired_tiles_file_path (str): path to a file with a list of expired tiles to be rendered
    """
    command = fr'cat {currently_expired_tiles_file_path} | /src/mod_tile/render_expired --map=osm --min-zoom={TILE_EXPIRE_MIN_ZOOM} --touch-from={TILE_EXPIRE_MIN_ZOOM}'
    run_command(command, process_log.debug, process_log.info, handle_command_graceful_exit, handle_command_successful_complete)


def run_apache_service():
    """
    Start apache tile serving service
    """
    command = 'apachectl -D FOREGROUND'
    run_command_async(command, process_log.info, process_log.info, handle_command_graceful_exit, handle_command_successful_complete)
    log.info('apache2 service started')


def run_renderd_service():
    """
    Start renderd service
    """
    command = 'renderd -f -c /usr/local/etc/renderd.conf'
    run_command_async(command, process_log.info, process_log.info, handle_command_graceful_exit, handle_command_successful_complete)
    log.info('renderd service started')


def configure_carto_project():
    log.info('configuring the carto project')
    with open(CARTO_FILE, 'r') as file :
      carto_data = file.read()

    for placeholder, value in db_config.items():
      carto_data = carto_data.replace(placeholder, value)

    with open(CARTO_FILE, 'w') as file:
      file.write(carto_data)

    command = 'carto {} > /src/openstreetmap-carto/mapnik.xml'.format(CARTO_FILE)
    run_command(command, process_log.info, process_log.info, handle_command_graceful_exit, handle_command_successful_complete)

def main():
    log.info('mod-tile container started')

    state_file_path = path.join(EXPIRED_DIRECTORY, 'state.txt')
    currently_expired_tiles_file_path = path.join(EXPIRED_DIRECTORY, 'currentlyExpired.list')
    rendered_state_file_path = path.join(EXPIRED_DIRECTORY, 'renderedState.txt')

    configure_carto_project()
    run_apache_service()
    run_renderd_service()
    expire_tiles(state_file_path, currently_expired_tiles_file_path, rendered_state_file_path)


def handle_command_graceful_exit(exit_code):
    process_log.error(f'process failed with exit code: {exit_code}')
    sys.exit(exit_code)


def handle_command_successful_complete():
    process_log.info(f'process completed successfully')


if __name__ == '__main__':
    log_file_extention = '.log'
    rendered_name = 'rendered'
    base_log_path = path.join('/var/log', app_name)
    service_logs_path = path.join(base_log_path, app_name + log_file_extention)
    mod_tile_log_path = path.join(base_log_path, rendered_name + log_file_extention)
    makedirs(base_log_path, exist_ok=True)
    log = generate_logger(app_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': service_logs_path},{ 'type': 'stream', 'output': 'stderr' }])
    process_log = generate_logger(rendered_name, log_level='INFO', handlers=[{'type': 'rotating_file', 'path': mod_tile_log_path}, { 'type': 'stream', 'output': 'stderr' }])

    main()
