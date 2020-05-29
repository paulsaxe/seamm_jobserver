# -*- coding: utf-8 -*-

"""Run the JobServer as a standalone.

"""

import asyncio
import configargparse
import logging
from pathlib import Path

import seamm_jobserver

logger = logging.getLogger(__name__)


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

    args, unknown = parser.parse_known_args()

    # Set up logging level to WARNING by default, going more verbose
    # for each new -v, to INFO and then DEBUG and finally ALL with 3 -v's

    numeric_level = max(3 - args.verbose_count, 0) * 10
    logging.basicConfig(level=numeric_level)

    # Create the working directory where files, output, etc. go.
    # At the moment this is datastore/job_id

    datastore = Path(args.datastore).expanduser()
    db_path = datastore / 'seamm.db'

    jobserver = seamm_jobserver.JobServer(
        db_path=db_path, check_interval=args.check_interval
    )

    asyncio.run(jobserver.start())


if __name__ == "__main__":
    run()
