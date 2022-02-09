# -*- coding: utf-8 -*-

"""Run the JobServer as a standalone.

"""

import asyncio
import logging
from pathlib import Path

import seamm_util
import seamm_jobserver

logger = logging.getLogger("JobServer")


def run():
    """The standalone JobServer app."""

    parser = seamm_util.seamm_parser("JobServer")

    parser.add_parser("JobServer")

    parser.add_argument(
        "JobServer",
        "--log-level",
        default="WARNING",
        type=str.upper,
        choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=(
            "The level of informational output for jobs, defaults to " "'%(default)s'"
        ),
    )

    parser.add_argument(
        "JobServer",
        "--check-interval",
        default=5,
        action="store",
        help="The interval for checking for new jobs.",
    )

    parser.add_argument(
        "JobServer",
        "--log-file",
        default="${SEAMM:root}/logs/jobserver.log",
        action="store",
        help="Where to save the logs.",
    )

    # Get the options
    parser.parse_args()
    options = parser.get_options("JobServer")
    seamm_options = parser.get_options("SEAMM")
    ini_files_used = parser.get_ini_files()

    # Make sure the logs folder exists (avoid FileNotFoundError)
    logfile = Path(options["log_file"])

    # Setup the logging
    if "log_level" in options:
        logging.basicConfig(level=options["log_level"], filename=logfile)

    # Set the logging level for the JobServer itself
    logger.setLevel(seamm_options["log_level"])

    # Where is the datastore?
    datastore = Path(seamm_options["datastore"]).expanduser()

    # Get the database file / instance
    db_path = datastore / "seamm.db"

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
    print("")

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
    logger.info("")

    jobserver = seamm_jobserver.JobServer(
        db_path=db_path, check_interval=options["check_interval"], logger=logger
    )

    asyncio.run(jobserver.start())


if __name__ == "__main__":
    run()
