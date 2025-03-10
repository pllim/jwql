""" Logging functions for the ``jwql`` automation platform.

This module provides decorators to log the execution of modules.  Log
files are written to the ``logs/`` directory in the ``jwql`` central
storage area, named by module name and timestamp, e.g.
``monitor_filesystem/monitor_filesystem_2018-06-20-15:22:51.log``


Authors
-------

    - Catherine Martlin
    - Alex Viana (wfc3ql Version)
    - Matthew Bourque
    - Jason Neal

Use
---

    To log the execution of a module, use:
    ::

        import os
        import logging

        from jwql.logging.logging_functions import configure_logging
        from jwql.logging.logging_functions import log_info
        from jwql.logging.logging_functions import log_fail

        @log_info
        @log_fail
        def my_main_function():
            pass

        if __name__ == '__main__':

            module = os.path.basename(__file__).replace('.py', '')
            configure_logging(module)

            my_main_function()

Dependencies
------------

    The user must have a configuration file named ``config.json``
    placed in the ``jwql`` directory and it must contain keys for
    ``log_dir`` and ``admin_account``.

References
----------
    This code is adopted and updated from python routine
    ``logging_functions.py`` written by Alex Viana, 2013 for the WFC3
    Quicklook automation platform.
"""

import datetime
import getpass
import importlib
import logging
import logging.config
import os
import pwd
import socket
import subprocess
import sys
import time
import traceback

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from functools import wraps

from jwql.utils.permissions import set_permissions
from jwql.utils.utils import get_config, ensure_dir_exists


def filter_maker(level):
    """
    This creates a logging filter that takes in an integer describing log level (with
    DEBUG being the lowest value and CRITICAL the highest), and returns True if and only
    if the logged message has a lower level than the filter level.

    The filter is needed because the logging system is designed so that it outputs
    messages of LogLevel *or higher*, because the assumption is you want to know if
    something happens that's more serious than what you're looking at.

    In this case, though, we're dividing printed-out log messages between the built-in
    STDOUT and STDERR output streams, and we have assigned ERROR and above to go to
    STDERR, while INFO and above go to STDOUT. So, by default, anything at ERROR or at
    CRITICAL would go to *both* STDOUT and STDERR. This function lets you add a filter
    that returns false for anything with a level above WARNING, so that STDOUT won't
    duplicate those messages.
    """
    level = getattr(logging, level)

    def filter(record):
        return record.levelno <= level

    return filter


def configure_logging(module):
    """
    Configure the log file with a standard logging format. The format in question is
    set up as follows:

    - DEBUG messages are ignored
    - INFO and WARNING messages go to both the log file and sys.stdout
    - ERROR and CRITICAL messages go to both the log file and sys.stderr
    - existing loggers are disabled before this configuration is applied

    Parameters
    ----------
    module : str
        The name of the module being logged.
    production_mode : bool
        Whether or not the output should be written to the production
        environement.
    path : str
        Where to write the log if user-supplied path; default to working dir.

    Returns
    -------
    log_file : str
        The path to the file where the log is written to.
    """

    # Determine log file location
    log_file = make_log_file(module)

    # Get the logging configuration dictionary
    logging_config = get_config()['logging']

    # Set the log file to the file that we got above
    logging_config["handlers"]["file"]["filename"] = log_file

    # Configure the logging system and set permissions for the file
    logging.config.dictConfig(logging_config)
    print('Log file initialized to {}'.format(log_file))
    set_permissions(log_file)

    return log_file


def get_log_status(log_file):
    """Returns the end status of the given ``log_file`` (i.e.
    ``SUCCESS`` or ``FAILURE``)

    Parameters
    ----------
    log_file : str
        The path to the file where the log is written to

    Returns
    -------
    status : bool
        The status of the execution of the script described by the log
        file (i.e. ``SUCCESS`` or ``FAILURE``)
    """

    with open(log_file, 'r') as f:
        data = f.readlines()
    last_line = data[-1].strip()

    if 'Completed Successfully' in last_line:
        return 'SUCCESS'
    else:
        return 'FAILURE'


def make_log_file(module):
    """Create the log file name based on the module name.

    The name of the ``log_file`` is a combination of the name of the
    module being logged and the current datetime.

    Parameters
    ----------
    module : str
        The name of the module being logged.
    production_mode : bool
        Whether or not the output should be written to the production
        environment.
    path : str
        Where to write the log if user-supplied path; default to
        working dir.

    Returns
    -------
    log_file : str
        The full path to where the log file will be written to.
    """

    # Build filename
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    hostname = socket.gethostname()
    filename = '{0}_{1}_{2}.log'.format(module, hostname, timestamp)

    # Determine save location
    user = pwd.getpwuid(os.getuid()).pw_name
    admin_account = get_config()['admin_account']
    log_path = get_config()['log_dir']

    # For production
    if user == admin_account and socket.gethostname()[0] == 'p':
        log_file = os.path.join(log_path, 'ops', module, filename)

    # For test
    elif user == admin_account and socket.gethostname()[0] == 't':
        log_file = os.path.join(log_path, 'test', module, filename)

    # For dev
    elif user == admin_account and socket.gethostname()[0] == 'd':
        log_file = os.path.join(log_path, 'dev', module, filename)

    # For local (also write to dev)
    else:
        log_file = os.path.join(log_path, 'dev', module, filename)

    # Make sure parent directory exists
    ensure_dir_exists(os.path.dirname(log_file))

    return log_file


def log_info(func):
    """Decorator to log useful system information.

    This function can be used as a decorator to log user environment
    and system information. Future packages we want to track can be
    added or removed as necessary.

    Parameters
    ----------
    func : func
        The function to decorate.

    Returns
    -------
    wrapped : func
        The wrapped function.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):

        # Log environment information
        logging.info('User: ' + getpass.getuser())
        logging.info('System: ' + socket.gethostname())
        logging.info('Python Version: ' + sys.version.replace('\n', ''))
        logging.info('Python Executable Path: ' + sys.executable)
        logging.info('Running as PID {}'.format(os.getpid()))

        # Read in setup.py file to build list of required modules
        toml_file = os.path.join(os.path.dirname(get_config()['setup_file']), 'pyproject.toml')
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)

        required_modules = data['project']['dependencies']

        # Clean up the module list
        module_list = [item.strip().replace("'", "").replace(",", "").split("=")[0].split(">")[0].split("<")[0] for item in required_modules]

        # Log common module version information
        for module in module_list:
            try:
                mod = importlib.import_module(module)
                logging.info(module + ' Version: ' + importlib.metadata.version(module))
                logging.info(module + ' Path: ' + mod.__path__[0])
            except (ImportError, AttributeError) as err:
                logging.warning(err)

        # nosec comment added to ignore bandit security check
        try:
            environment = subprocess.check_output('conda env export', universal_newlines=True, shell=True)  # nosec
            logging.info('Environment:')
            for line in environment.split('\n'):
                logging.info(line)
        except Exception as err:   # catch any exception and report the entire traceback
            logging.exception(err)

        # Call the function and time it
        t1_cpu = time.perf_counter()
        t1_time = time.time()
        func(*args, **kwargs)
        t2_cpu = time.perf_counter()
        t2_time = time.time()

        # Log execution time
        hours_cpu, remainder_cpu = divmod(t2_cpu - t1_cpu, 60 * 60)
        minutes_cpu, seconds_cpu = divmod(remainder_cpu, 60)
        hours_time, remainder_time = divmod(t2_time - t1_time, 60 * 60)
        minutes_time, seconds_time = divmod(remainder_time, 60)
        logging.info('Elapsed Real Time: {}:{}:{}'.format(int(hours_time), int(minutes_time), int(seconds_time)))
        logging.info('Elapsed CPU Time: {}:{}:{}'.format(int(hours_cpu), int(minutes_cpu), int(seconds_cpu)))

    return wrapped


def log_fail(func):
    """Decorator to log crashes in the decorated code.

    Parameters
    ----------
    func : func
        The function to decorate.

    Returns
    -------
    wrapped : func
        The wrapped function.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):

        try:

            # Run the function
            func(*args, **kwargs)
            logging.info('Completed Successfully')

        except Exception:
            logging.critical(traceback.format_exc())
            logging.critical('CRASHED')

    return wrapped


def log_timing(func):
    """Decorator to time a module or function within a code.

    Parameters
    ----------
    func : func
        The function to time.

    Returns
    -------
    wrapped : func
        The wrapped function. Will log the time."""

    def wrapped(*args, **kwargs):

        # Call the function and time it
        t1_cpu = time.process_time()
        t1_time = time.time()
        func(*args, **kwargs)
        t2_cpu = time.process_time()
        t2_time = time.time()

        # Log execution time
        hours_cpu, remainder_cpu = divmod(t2_cpu - t1_cpu, 60 * 60)
        minutes_cpu, seconds_cpu = divmod(remainder_cpu, 60)
        hours_time, remainder_time = divmod(t2_time - t1_time, 60 * 60)
        minutes_time, seconds_time = divmod(remainder_time, 60)
        logging.info('Elapsed Real Time of {}: {}:{}:{}'.format(func.__name__, int(hours_time), int(minutes_time), int(seconds_time)))
        logging.info('Elapsed CPU Time of {}: {}:{}:{}'.format(func.__name__, int(hours_cpu), int(minutes_cpu), int(seconds_cpu)))

    return wrapped
