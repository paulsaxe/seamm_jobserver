# -*- coding: utf-8 -*-

"""The JobServer for the SEAMM environment.

"""

import asyncio

# import concurrent.futures
from datetime import datetime, timezone
import functools
import json
import logging
import multiprocessing
import sqlite3

from seamm import run_flowchart

logger = logging.getLogger(__name__)


class JobServer(object):
    def __init__(self, db_path=None, check_interval=5, logger=logger):
        """Initialize the instance

        Parameters
        ----------
        check_interval : integer
            Number of seconds between checks for new jobs in the database
        """
        super().__init__()

        self.logger = logger
        self.stop = False
        self._db = None
        self._db_path = None
        self.check_interval = check_interval
        self._tasks = set()
        self._jobs = {}

        # This will open the database if it is given.
        self.db_path = db_path

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, value):
        if value != self._db_path:
            # Close any connection to the database
            if self._db is not None:
                self._db.close()
                self._db = None
            if value is not None:
                self.logger.info(f"Opening the database '{value}'")
                self._db = sqlite3.connect(value)
            self._db_path = value

    @property
    def db(self):
        return self._db

    async def start(self):
        """Start the main event loop."""

        while not self.stop:
            # If nothing to do sleep and then check for new jobs
            if len(self._tasks) == 0:
                await asyncio.sleep(self.check_interval)
            else:
                done, pending = await asyncio.wait(
                    self._tasks,
                    timeout=self.check_interval,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                self._tasks = pending

                for task in done:
                    result = task.result()
                    self.logger.info("Task finished, result = {}".format(result))

            self.check_for_finished_jobs()
            self.check_for_new_jobs()

    def add_task(self, coroutine):
        """Add a new task to the queue.

        Parameters
        ----------
        coroutine : asyncio coroutine
            The coroutine to add as a task
        """
        self._tasks.add(asyncio.create_task(coroutine))

    def add_blocking_task(self, coroutine, *args, **kwargs):
        """Add a new task to the queue, running in another thread

        Parameters
        ----------
        coroutine : asyncio coroutine
            The coroutine to add as a task
        """
        loop = asyncio.get_running_loop()
        self._tasks.add(loop.run_in_executor(None, functools.partial(coroutine, *args)))

    def check_for_new_jobs(self):
        """Check the database for new jobs that are runnable."""
        cursor = self.db.cursor()

        self.logger.debug("Checking jobs in datastore")
        cursor.execute(
            "SELECT id, path, json_extract(parameters, '$.cmdline')"
            "  FROM jobs"
            " WHERE status = 'submitted'"
        )
        while True:
            result = cursor.fetchone()
            if result is None:
                break
            job_id, path, cmdline = result
            cmdline = json.loads(cmdline)

            current_time = datetime.now(timezone.utc)
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE jobs SET status='running', started = ? WHERE id = ?",
                (current_time, job_id),
            )
            self.db.commit()

            print(f"Starting job {job_id} at {path}")

            self.start_job(job_id, path, cmdline)

    def start_job(self, job_id, wdir, cmdline=""):
        """Run the given job.

        Parameters
        ----------
        job_id : integer
            The id of the job to run.
        """
        self.logger.info("Starting job {}".format(job_id))

        process = multiprocessing.Process(
            target=run_flowchart,
            kwargs={
                "job_id": job_id,
                "wdir": wdir,
                "in_jobserver": True,
                "cmdline": cmdline,
            },
            name="Job_{:06d}".format(job_id),
        )
        self._jobs[job_id] = process
        process.start()
        self.logger.info("   pid = {}".format(process.pid))

    def check_for_finished_jobs(self):
        """Check whether jobs have finished."""
        finished = []
        for job_id, process in self._jobs.items():
            if process.is_alive():
                self.logger.debug("Job {} is running".format(job_id))
            else:
                finished.append(job_id)
                status = process.exitcode
                process.close()
                self.logger.info("Job {} finished, code={}.".format(job_id, status))
                print(f"Job {job_id} finished.")
                cursor = self.db.cursor()
                current_time = datetime.now(timezone.utc)
                cursor.execute(
                    "UPDATE jobs SET status='finished', finished = ? " "WHERE id = ?",
                    (current_time, job_id),
                )
                self.db.commit()
        for job_id in finished:
            del self._jobs[job_id]
