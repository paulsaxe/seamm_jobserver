# -*- coding: utf-8 -*-

"""Run the JobServer as a standalone.

"""

import asyncio
import logging
from pathlib import Path

import seamm
import seamm_jobserver

logger = logging.getLogger('JobServer')


def run():
    """The standalone JobServer app.
    """

    parser = seamm.getParser(
        ini_files=[
            'etc/seamm/jobserver.ini',
            '~/.seamm/jobserver.ini',
            'jobserver.ini'
        ],
    )  # yapf: disable

    parser.add_parser('JobServer')

    parser.add_argument(
        'JobServer',
        '--log-level',
        default='WARNING',
        type=str.upper,
        choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help=(
            "The level of informational output, defaults to "
            "'%(default)s'"
        )
    )

    parser.add_argument(
        'JobServer',
        '--job-log-level',
        default='WARNING',
        type=str.upper,
        choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help=(
            "The level of informational output for jobs, defaults to "
            "'%(default)s'"
        )
    )

    parser.add_argument(
        'JobServer',
        "--datastore",
        dest="datastore",
        default='.',
        action="store",
        help="The datastore (directory) for this run."
    )

    parser.add_argument(
        'JobServer',
        "--check-interval",
        default=5,
        action="store",
        help="The interval for checking for new jobs."
    )

    parser.add_argument(
        'JobServer',
        "--log-file",
        default='${datastore}/logs/jobserver.log',
        action="store",
        help="Where to save the logs."
    )

    # Get the options
    parser.parse_args()
    options = parser.get_options('JobServer')
    ini_files_used = parser.get_ini_files()

    # Where is the datastore?
    datastore = Path(options['datastore']).expanduser()

    # Make sure the logs folder exists (avoid FileNotFoundError)
    logfile = Path(options['log_file'])

    # Setup the logging
    if 'log_level' in options:
        logging.basicConfig(level=options['job_log_level'], filename=logfile)

    # Set the logging level for the JobServer itself
    logger.setLevel(options['log_level'])

    # Get the database file / instance
    db_path = datastore / 'seamm.db'

    jobserver = seamm_jobserver.JobServer(
        db_path=db_path,
        check_interval=options['check_interval'],
        logger=logger
    )

    print(f"The JobServer is starting in {Path.cwd()}")
    print(f"           version = {seamm_jobserver.__version__}")
    print(f"         datastore = {db_path}")
    print(f"    check interval = {options['check_interval']}")
    print(f"          log file = {logfile}")

    if len(ini_files_used) == 0:
        print("No .ini files were used")
    else:
        print("The following .ini files were used:")
        for filename in ini_files_used:
            print(f"    {filename}")
    print('')

    logger.info(f"The JobServer is starting in {Path.cwd()}")
    logger.info(f"           version = {seamm_jobserver.__version__}")
    logger.info(f"         datastore = {db_path}")
    logger.info(f"    check interval = {options['check_interval']}")
    logger.info(f"          log file = {logfile}")

    if len(ini_files_used) == 0:
        logger.info("No .ini files were used")
    else:
        logger.info("The following .ini files were used:")
        for filename in ini_files_used:
            logger.info(f"    {filename}")
    logger.info('')

    asyncio.run(jobserver.start())


if __name__ == "__main__":
    run()
