import re
import subprocess
import sys
import time
from os import path, linesep, environ, mkdir
from jsonlogger.logger import JSONLogger

SEQUENCE_PATH_DENOMINATORS = [1000000, 1000, 1]

INITIAL_TIMEOUT = int(environ.get('INITIAL_TIMEOUT', 30))
RENDER_EXPIRED_TILES_INTERVAL = float(
    environ.get('RENDER_EXPIRED_TILES_INTERVAL', 60))
EXPIRED_DIR = environ.get('EXPIRED_DIR', '/mnt/expired')

environ['PGHOST'] = environ['POSTGRES_HOST']
environ['PGPORT'] = environ['POSTGRES_PORT']
environ['PGDATABASE'] = environ['POSTGRES_DB']
environ['PGUSER'] = environ['POSTGRES_USER']
environ['PGPASSWORD'] = environ['POSTGRES_PASSWORD']


def run_subprocess(args, log_output=True):
    """
    Run a subprocess from the passed args
    Args:
        args (string|list): the command to run as a string or a list of strings of the command with arguments
        log_output (bool, optional): whether to log output of the subprocess. Defaults to True.
    Returns:
        subprocess.CompletedProcess: subprocess response object
    """
    try:
        process = subprocess.run(args, shell=True, encoding='utf8', check=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(environ))
    except (subprocess.CalledProcessError, Exception) as ex:
        log.error(fr'The subprocess raised an error: {ex.stderr}')
        raise
    else:
        if log_output:
            if process.stdout and len(process.stdout) > 0:
                [log.info(log_line) for log_line in process.stdout.split(
                    '\n') if len(log_line) > 0]
            if process.stderr and len(process.stderr) > 0:
                [log.error(log_line) for log_line in process.stderr.split(
                    '\n') if len(log_line) > 0]
        return process


def extract_positivie_integer_value(text, key):
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
    try:
        integer_value = int(value)
        if integer_value < 0:
            raise ValueError()
    except ValueError:
        raise ValueError(
            f'"{key}=" must be followed by a positive integer in text')

    return integer_value


def unique_tiles_from_files(start, end, directory):
    """
    Reads z/x/y tiles (e.g. 0/0/0) from files, in a structured replication dir.
    The functions returns a unique, ordered list of these tiles
    Args:
        start (int): index of the first replication file
        end (int): index of the last replication file
        directory (str): replication directory path
    Returns:
        list: unique and ordered list of tiles
    """
    expired_tiles = []
    i = start

    # replication directory structure 004/215/801.state.txt corresponds to index 4,215,801
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
        except:
            raise
        finally:
            i += 1

    expired_tiles = list(set(expired_tiles))
    expired_tiles.sort()
    return expired_tiles


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


def expire_tiles(state_file_path, currently_expired_tiles_file_path, rendered_state_file_path):
    """
    Call mod_tile's render_expired with tiles that need to be re-rendered
    Args:
        state_file_path (str): path to a state file that holds the current replication state defined by the sequence number
        currently_expired_tiles_file_path (str): path to currentlyExpired.list file that holds a list of tiles to be re-rendered
        rendered_state_file_path (str): path to a file that holds the current rendered state relative to sequence number
    """
    action_id = 1  # identifier for each loop

    # Infinite loop that sleeps between tiles expirations
    while True:
        try:
            with open(state_file_path, 'r') as state_file:
                end = extract_positivie_integer_value(state_file.read(), 'sequenceNumber')
                if not end:
                    raise LookupError(f'"sequenceNumber=" is not present in file')
            
            with open(rendered_state_file_path, 'r') as rendered_file:
                start = extract_positivie_integer_value(rendered_file.read(), 'lastRendered')

            log.info(f'current rendering state is lastRendered={start}, sequenceNumber={end}', extra={"action_id": action_id})
        except FileNotFoundError as e:
            if e.filename == rendered_state_file_path:
                log.info('initializing rendering state file', extra={"action_id": action_id})
                start = 1
                with open(rendered_state_file_path, 'w') as rendered_file:
                    rendered_file.write('lastRendered=1')
            else:
                log.error(f'{e.strerror} - {e.filename}')
        except:
            raise
        else:
            if start <= end:
                expired_tiles = unique_tiles_from_files(start, end, EXPIRED_DIR)
                update_currently_expired_tiles_file(currently_expired_tiles_file_path, expired_tiles)
                if len(expired_tiles) > 0:
                    render_expired(currently_expired_tiles_file_path)
                update_rendered_state_file(rendered_state_file_path, end)
        finally:
            action_id += 1
            time.sleep(RENDER_EXPIRED_TILES_INTERVAL)


def render_expired(currently_expired_tiles_file_path):
    """
    Render expired tiles
    Args:
        currently_expired_tiles_file_path (str): path to a file with a list of expired tiles to be rendered
    """
    # TODO: consider extracting map, min-zoom and touch-from env var
    _ = run_subprocess(
        fr'cat {currently_expired_tiles_file_path} | /src/mod_tile/render_expired --map=osm --min-zoom=8 --touch-from=8 >/dev/null')
    log.info('rendered expired tiles')


def get_external_data():
    """
    Populate openstreetmap-carto's external data sources to postgresql
    """
    log.info('getting external data')
    _ = run_subprocess('PGPASSWORD=$POSTGRES_PASSWORD /src/openstreetmap-carto/scripts/get-external-data.py -H $POSTGRES_HOST -d $POSTGRES_DB -p 5432 -U $POSTGRES_USER -c /src/openstreetmap-carto/external-data.yml')


def run_apache_service():
    """
    Start apache tile serving service
    """
    _ = run_subprocess('service apache2 start')
    log.info('apache2 service started')


def run_renderd_service():
    """
    Start renderd service
    """
    _ = run_subprocess('renderd -c /usr/local/etc/renderd.conf')
    log.info('renderd service started')


def main():
    log.info('mod-tile container started')

    state_file_path = path.join(EXPIRED_DIR, 'state.txt')
    currently_expired_tiles_file_path = path.join(
        EXPIRED_DIR, 'currentlyExpired.list')
    rendered_state_file_path = path.join(EXPIRED_DIR, 'renderedState.txt')

    # TODO: replace with a better logic, perhaps make container dependendant in docker-compose
    time.sleep(INITIAL_TIMEOUT)
    get_external_data()
    run_apache_service()
    run_renderd_service()
    # TODO: add liveness and readiness probes
    expire_tiles(state_file_path, currently_expired_tiles_file_path, rendered_state_file_path)


if __name__ == '__main__':
    # create a dir for the default log file location
    mkdir('/var/log/osm-seed')
    # pass service/process name as a parameter to JSONLogger to be as an identifier for this specific logger instance
    log = JSONLogger('main-debug', additional_fields={'service': 'mod-tile'})
    main()