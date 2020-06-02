# -*- coding: utf-8 -*-

"""Run the JobServer as a standalone.

"""

import asyncio
import logging
from pathlib import Path

import configargparse

import seamm_jobserver

logger = logging.getLogger('JobServer')


def run():
    """The standalone JobServer app.
    """

    parser = configargparse.ArgParser(
        auto_env_var_prefix='',
        default_config_files=[
            '/etc/seamm/seamm.ini',
            '~/.seamm/seamm.ini',
        ],
        description='Run the JobServer standalone'
    )

    parser.add_argument(
        '--seamm-configfile',
        is_config_file=True,
        default=None,
        help='a configuration file to override others'
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose_count",
        action="count",
        default=0,
        help="increases log verbosity for each occurence."
    )
    parser.add_argument(
        "--datastore",
        dest="datastore",
        default='.',
        action="store",
        env_var='SEAMM_DATASTORE',
        help="The datastore (directory) for this run."
    )
    parser.add_argument(
        "--check-interval",
        default=5,
        action="store",
        help="The interval for checking for new jobs."
    )
    parser.add_argument(
        "--jobserver-logfile",
        default='%datastore%/logs/jobserver.log',
        action="store",
        help="Where to save the logs. "
    )
    parser.add_argument(
        "--jobserver-log-level",
        default='INFO',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
        type=str.upper,
        help="The logging level for the JobServer."
    )

    options, unknown = parser.parse_known_args()

    # Where is the datastore?
    datastore = Path(options.datastore).expanduser()

    # Make sure the logs folder exists (avoid FileNotFoundError)
    logfile = Path(
        options.jobserver_logfile.replace('%datastore%', str(datastore))
    )

    # Setup overall logging level to WARNING by default, going more verbose
    # for each new -v, to INFO and then DEBUG and finally ALL with 3 -v's

    numeric_level = max(3 - options.verbose_count, 0) * 10
    logging.basicConfig(level=numeric_level, filename=logfile)

    # Set the logging level for the JobServer itself
    logger.setLevel(options.jobserver_log_level)

    # Get the database file / instance
    db_path = datastore / 'seamm.db'

    jobserver = seamm_jobserver.JobServer(
        db_path=db_path, check_interval=options.check_interval, logger=logger
    )

    asyncio.run(jobserver.start())


if __name__ == "__main__":
    run()
