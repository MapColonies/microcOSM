#!/usr/bin/env python3
import os
import shutil
import sys
import re
import requests
import pytz
import pause

from os import environ
from enum import Enum
from datetime import datetime, timedelta, timezone
from osmeterium.run_command import run_command
from jsonlogger.logger import JSONLogger

DATA_FOLDER = 'data'
CONFIGURATION_FILE = 'configuration.txt'
STATE_FILE = 'state.txt'
REPLICATION_DIR = '/mnt/data'
CONFIG_DIR = '/app/config'
OSMOSIS_DIR='osmosis'
OSMOSIS_TIME_ZONE = 'UTC'
REPLICATION_TOP_DIR_DIVIDER = 1000000
REPLICATION_BOTTOM_DIR_DIVIDER = 1000
REPLICATION_STATE_FILE_MODULO = 1000
MERGE_CONFIG_BASE_URL_HEADER = '=file://'
SEQUENCE_NUMBER = 'sequenceNumber'
MERGE_CONFIG_MAP = {
    'BASE_URL': 'baseUrl',
    'INTERVAL_LENGTH': 'intervalLength',
    'MAX_INTERVAL': 'maxInterval'
}
Time_Unit = Enum('Time_Unit', 'minute hour day week')
log = None

TIME_UNIT_TO_MERGE = environ.get('TIME_UNIT_TO_MERGE')
TIME_UNIT_BASED_ON = environ.get('TIME_UNIT_BASED_ON')
REPLICATION_URL = environ.get('REPLICATION_URL')

class TimeUnit:
    def __init__(self, name, config_path):
        self.name = name
        config_content = read_file(config_path, True)
        config_values = parse_time_unit_config(config_content)
        self.interval_length = config_values['interval_length']
        self.max_interval = config_values['max_interval']
        self.sub_time_unit_data_dir = config_values['sub_time_unit_data_dir']

    def get_path(self):
        return os.path.join(REPLICATION_DIR, self.name)
    
    def __str__(self):
        result = f'time unit: {self.name}\n'
        result += f'based on: {TIME_UNIT_BASED_ON}\n'
        result += f'interval length: {self.interval_length}\n'
        result += f'max interval: {self.max_interval}\n'
        result += f'sub time unit data directory: {self.sub_time_unit_data_dir}'
        return result

def handle_osmosis_exit_code(exit_code):
    log.error(fr'Osmosis raised an error: {exit_code}')
    raise

def read_file(file_path, throw_not_found=False):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as opened_file:
            file_content = opened_file.read()
        return file_content
    else:
        log.error(f'file {file_path} not found')
        if throw_not_found:
            raise FileNotFoundError(f'could not find the file on the specified path: {file_path}')

def overwrite_file(file_path, content, throw_exception=True):
    try:
        with open(file_path, 'w') as file_to_overwrite:
            file_to_overwrite.write(content)
    except:
        error = (f'could not overwrite the file on the specified path: {file_path}')
        if throw_exception:
            log_and_exit(error)
        log.error(error)

def parse_integer_to_directory_number(integer):
    if integer < 0:
        raise ValueError()
    return '{0:0=3d}'.format(integer)

def construct_directory_path_from_integer(integer):
    return (parse_integer_to_directory_number(int(integer / REPLICATION_TOP_DIR_DIVIDER)),
            parse_integer_to_directory_number(int(integer / REPLICATION_BOTTOM_DIR_DIVIDER)),
            parse_integer_to_directory_number(int(integer % REPLICATION_STATE_FILE_MODULO)))

def copy_only_if_not_exist(src, dst):
    if not os.path.isfile(dst):
        shutil.copy(src, dst)

def log_and_exit(exception_message):
    log.error(exception_message)
    sys.exit(1)

def get_file_from_server(path):
    (is_ok, file_content) = request_file_from_url(REPLICATION_URL, path)
    if (not is_ok):
        log.error(
            f'file not found in remote server {REPLICATION_URL}.')
        return None
    return file_content

def request_file_from_url(server_url, path):
    url = '/'.join([server_url, path])
    log.info(f'fetching file from {url}')
    result = requests.get(url)
    return (result.ok, result.text)

def extract_positive_number(file_content, key):
    try:
        value = extract_value(content=file_content, key=key, is_int_value=True, delimiter='=', 
                                throw_not_found=False, default_value=0)
        if value < 0:
            raise ValueError()
        return value
    except:
        log_and_exit(f'{key} must be a positive integer')

def time_zone_to_utc(datetime):
    time_zone_dt = pytz.timezone(OSMOSIS_TIME_ZONE).localize(datetime)
    return time_zone_dt.astimezone(pytz.utc)

def extract_value(content, key, is_int_value=True, delimiter='=', throw_not_found=False, default_value=-1):
    """
    Extracts a key from content, value can be an integer or string
    Args:
        content (str): the full given text content
        key (str): the wanted key to be searched in the given content
        is_int_value (bool): determines if the key's value is int or string, which effects the search and parsing of the value
        delimiter (str): the separator between the key and it's value to be splitted by
        throw_not_found (bool): a flag determines if to raise a LookupError
        default_value (any): the value returned upon not finding the key in the content while not throwing an error
    Raises:
        LookupError: throw_not_found is true and key could not be found
        ValueError: is_int_value is true and the value is not a positive integer or an error while parsing the value
    Returns:
        (int|str): the extracted value
    """
    if is_int_value:
        match = re.search(fr'{key}=\d+', content)
    else:
        match = re.search(fr'{key}=\S+', content)
    if not match:
        if throw_not_found:
            raise LookupError(f'"{key}=" is not present in the given content')
        else:
            return default_value
    
    value = match.group(0).split(delimiter)[1]
    try:
        return int(value) if is_int_value else str(value)
    except ValueError:
        raise ValueError('an error accourd while extraction.')

def parse_time_unit_config(config_content, fetch_from_file_system = False):
    """
    Extracts the wanted values from a time unit config
    Args:
        config_content (str): the config text
        fetch_from_file_system: (bool): flag
    Returns:
        Dictionary: key value pair extracted from config
    """
    interval_length = extract_positive_number(config_content, MERGE_CONFIG_MAP['INTERVAL_LENGTH'])
    max_interval = extract_positive_number(config_content, MERGE_CONFIG_MAP['MAX_INTERVAL'])
    if fetch_from_file_system:
        sub_time_unit_data_dir = extract_value(content=config_content, key=MERGE_CONFIG_MAP['BASE_URL'], is_int_value=False, delimiter=MERGE_CONF_BASE_URL_HEADER)
    else:
        sub_time_unit_data_dir = extract_value(content=config_content, key=MERGE_CONFIG_MAP['BASE_URL'], is_int_value=False, delimiter=REPLICATION_URL + '/')
    return { 'interval_length': interval_length, 'max_interval': max_interval, 'sub_time_unit_data_dir': sub_time_unit_data_dir }

def http_fetch_starting_state(time_unit):
    """
    Each TimeUnit first merge has to be set based on it's sub TimeUnit state file.
    The time unit replication files will be merged in its interval length from the first existing state of the sub time unit to the last one.
    This function will fetch that state file from the sub time unit
    Args:
        time_unit (TimeUnit): the TimeUnit to fetch starting state file for
    """
    sub_time_unit_state_dir = os.path.join(time_unit.sub_time_unit_data_dir, STATE_FILE)
    sub_time_unit_state_content = get_file_from_server(sub_time_unit_state_dir)
    if sub_time_unit_state_content is None:
        return False
    max_sequence_number = extract_positive_number(sub_time_unit_state_content, SEQUENCE_NUMBER)
    log.info(f'looking for the first state file between sequence number 0 to {max_sequence_number}')
    for i in range(max_sequence_number + 1):
        (top_dir, bottom_dir, state_value) = construct_directory_path_from_integer(i)
        first_state_file = os.path.join(time_unit.sub_time_unit_data_dir, top_dir, bottom_dir, f'{state_value}.state.txt')
        first_state_file_content = get_file_from_server(first_state_file)
        if first_state_file_content is None:
            continue
        log.info(f'found first state file in {first_state_file}')
        set_state_file_content(time_unit.get_path(), first_state_file_content)
        return True
    return False

def set_state_file_content(time_unit_dir, state_content):
    """
    Overwrites a timeunit state file in two levels, it's own replication and it's based upon state that it merges by.
    Used when initializing a time unit environment
    Args:
        time_unit_dir (str): the replication directory of the time unit
        state_content (str): the state file content that will be used in the override
    """
    time_unit_state_path = os.path.join(time_unit_dir, STATE_FILE)
    overwrite_file(time_unit_state_path, state_content)
    time_unit_data_state_path = os.path.join(time_unit_dir, DATA_FOLDER, STATE_FILE)
    overwrite_file(time_unit_data_state_path, state_content)

def init_time_unit_merge(time_unit):
    """
    Initializes the time unit replication merge environment if not already exists
    Args:
        time_unit (TimeUnit): the time unit to init its merge env
    """
    time_unit_state_path = os.path.join(time_unit.get_path(), STATE_FILE)
    if os.path.isfile(time_unit_state_path):
        return None
    os.makedirs(os.path.join(time_unit.get_path(), DATA_FOLDER), exist_ok=True)
    copy_time_unit_config(time_unit.name)
    log.info('initializing merge replication environment')
    found_first_state = False
    while not found_first_state:
        found_first_state = http_fetch_starting_state(time_unit)
        if found_first_state:
            log.info('initialized merge replication environment successfully')
            return None
        sleep_period = calculate_sleep_based_on_sub()
        if sleep_period is None:
            log_and_exit('could not find starting state based on the sub time unit. exiting script.')
        log.info('there are no sub time unit replications yet, going to sleep for {:.2f} seconds'.format(sleep_period))
        pause.seconds(sleep_period)

def copy_time_unit_config(time_unit_name):
    """
    Copies the time unit configuration instead of default one generated by osmosis
    Args:
        time_unit_name (str): the name of the time unit
    """
    time_unit_dir_path = os.path.join(REPLICATION_DIR, time_unit_name)
    time_unit_config_src = os.path.join(CONFIG_DIR, f'{time_unit_name}-config.txt')
    time_unit_config_dst = os.path.join(time_unit_dir_path, CONFIGURATION_FILE)
    shutil.copy(time_unit_config_src, time_unit_config_dst)

def calculate_sleep_based_on_sub(default_sleep_period = None):
    """
    In the case where merge env was not set yet and there are no merges from this time unit
    a loop trying to fetch the first state of the sub time unit is accouring.
    Between each try the sleep period will be calculated based on when the first sub time unit merge should accord.
    Args:
        default_sleep_period (float): in case something went wrong in the calculation the default value that will be set
    """
    try:
        sub_time_unit_conf_content = get_file_from_server(os.path.join(TIME_UNIT_BASED_ON, CONFIGURATION_FILE))
        if sub_time_unit_conf_content is None:
            raise
        sub_time_unit_interval = extract_positive_number(sub_time_unit_conf_content, MERGE_CONFIG_MAP['INTERVAL_LENGTH'])
        return get_sleep_period(TIME_UNIT_BASED_ON, sub_time_unit_interval, True)
    except:
        return default_sleep_period

def load_merge_configuration():
    """
    Sets the wanted TimeUnit to be merged on the job
    TimeUnit will be initialized with its configuration file
    """
    if TIME_UNIT_TO_MERGE not in Time_Unit._member_names_:
        raise
    time_unit = TimeUnit(TIME_UNIT_TO_MERGE, os.path.join(CONFIG_DIR, f'{TIME_UNIT_TO_MERGE}-config.txt'))
    log.info(f'time unit was loaded with the following configuration:{str(time_unit)}')
    return time_unit

def get_current_state_status(time_unit):
    """
    Gets the time unit's state status,
    containing the last last sub time unit sequence number and the actual time unit sequence nubmer
    Args:
        time_unit (TimeUnit): the timeunit object of this container
    Returns:
        (Dictionary): consisting the current status
    """
    time_unit_path = time_unit.get_path()
    time_unit_state = os.path.join(time_unit_path, STATE_FILE)
    time_unit_state_content = read_file(time_unit_state)
    time_unit_data_state = os.path.join(time_unit_path, DATA_FOLDER, STATE_FILE)
    time_unit_data_state_content = read_file(time_unit_data_state)
    current_state = { 
    'last_sub_sequence_number': extract_positive_number(time_unit_state_content, SEQUENCE_NUMBER),
    'sequence_number': extract_positive_number(time_unit_data_state_content, SEQUENCE_NUMBER)
    }
    return current_state

def get_last_state_timestamp(last_state_path, isHttp):
    """
    Fetching the last state file from remote server or file system and extracting the timestamp key
    Args:
        last_state_path (str): the path to the last state, could be url or file system
        isHttp (bool): flag determines if the last state should be fetched from file system or remote http server
    Retruns:
        (str): the timestamp of the last merge created in this time unit
    """
    try:
        if isHttp:
            last_state_content = get_file_from_server(last_state_path)
        else:
            last_state_content = read_file(last_state_path, True)
        return extract_value(content=last_state_content, key='timestamp', is_int_value=False, delimiter='=', throw_not_found=True)
    except:
        log.error(f'could not determine the last state timestamp from the path: {time_unit_path}')

def get_sleep_period(time_unit_path, interval, isHttp):
    """
    Calculates the time in seconds for the next merge job to be scheduled based on the last state timestamp
    which is the last merge of the current time unit that was created, and the interval between every merge.
    Args:
        time_unit_path (str): the path to the time unit
        interval (int): the interval merge of the time unit
        isHttp (bool): flag determines if the last state should be fetched from file system or remote http server
    Returns:
        delta (float): the seconds til the next merge job will be effective
    """
    try:
        last_state_path = os.path.join(time_unit_path, DATA_FOLDER, STATE_FILE)
        last_merge_timestamp = get_last_state_timestamp(last_state_path, isHttp)
        last_merge_datetime = datetime.strptime(last_merge_timestamp, r'%Y-%m-%dT%H\:%M\:%SZ')
        next_merge_datetime = last_merge_datetime + timedelta(seconds=interval)
        delta = (time_zone_to_utc(next_merge_datetime) - datetime.now(tz=timezone.utc)).total_seconds()
        if delta < 0:
            return 0
        return delta
    except:
        log_and_exit('could not determine sleep period for the next job to accord')

def scheduale_next_merge(time_unit):
    sleep_period = get_sleep_period(time_unit.get_path(), time_unit.interval_length, False)
    log.info('finished merge job successfully, next merge job is scheduled in {:.2f} seconds'.format(sleep_period))
    pause.seconds(sleep_period)

def merge_job_loop(time_unit):
    log.info('starting merge job')
    init_time_unit_merge(time_unit)
    while True:
        log.info(f'state before merge job: { get_current_state_status(time_unit) }')
        log.info('running osmosis merge-replication-files command')
        run_command(f'{OSMOSIS_DIR} --merge-replication-files workingDirectory={time_unit.get_path()}',
                    log.info,
                    log.error,
                    handle_osmosis_exit_code,
                    (lambda: log.info('Osmosis finished successfully.')))
        log.info(f'state after merge job: { get_current_state_status(time_unit) }')
        scheduale_next_merge(time_unit)

def main():
    log.info('replication-merger container started')
    try:
        time_unit = load_merge_configuration()
    except:
        log_and_exit(f'time unit {TIME_UNIT_TO_MERGE} cannot be merged.')
    merge_job_loop(time_unit)

if __name__ == '__main__':
    # create a dir for the default log file location
    os.makedirs('/var/log/osm-seed', exist_ok=True)
    # pass service/process name as a parameter to JSONLogger to be as an identifier for this specific logger instance
    log = JSONLogger('main-debug', additional_fields={'service': 'replication-merger'})
    main()