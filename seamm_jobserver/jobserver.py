# -*- coding: utf-8 -*-

"""The JobServer for the SEAMM environment.

"""

import asyncio
# import concurrent.futures
from datetime import datetime
import functools
import logging
import random
import sqlite3
import time

from seamm import run_flowchart

logger = logging.getLogger(__name__)


async def run_job(job_id):
    """Run the given job.

    Parameters
    ----------
    job_id : integer
        The id of the job to run.
    """
    logger.debug('Running job {}'.format(job_id))
    print('Running job {}'.format(job_id))

    t = random.randint(5, 25)
    logger.debug('  run will take {} seconds'.format(t))
    time.sleep(t)

    return {
        'task': 'ran job',
        'job_id': job_id
    }  # yapf: disable


class JobServer(object):

    def __init__(self, db_path=None, check_interval=5):
        """Initialize the instance

        Parameters
        ----------
        check_interval : integer
            Number of seconds between checks for new jobs in the database
        """
        super().__init__()

        self.stop = False
        self._db = None
        self._db_path = None
        self.check_interval = check_interval
        self._tasks = set()

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
                self._db = sqlite3.connect(value)
                # temporary!
                # cursor = self._db.cursor()
                # cursor.execute("UPDATE job SET status='Submitted'")
                # self.db.commit()
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
                self.check_for_jobs()
            else:
                done, pending = await asyncio.wait(
                    self._tasks,
                    timeout=self.check_interval,
                    return_when=asyncio.FIRST_COMPLETED
                )

                self._tasks = pending

                for task in done:
                    result = task.result()
                    logger.warning('Task finished, result = {}'.format(result))

                    if result['task'] == 'ran job':
                        job_id = result['job_id']
                        cursor = self.db.cursor()
                        cursor.execute(
                            "UPDATE job SET status='Finished', started = ? "
                            "WHERE id = ?", (datetime.utcnow(), job_id)
                        )
                        self.db.commit()
                        logger.warning('Job {} finished.'.format(job_id))

                self.check_for_jobs()

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
        self._tasks.add(
            loop.run_in_executor(None, functools.partial(coroutine, *args))
        )

    def check_for_jobs(self):
        """Check the database for new jobs that are runnable."""
        cursor = self.db.cursor()
        logger.debug("Checking jobs in datastore")
        cursor.execute("SELECT id, path FROM job WHERE status = 'Submitted'")
        while True:
            result = cursor.fetchone()
            if result is None:
                break
            job_id, path = result
            logger.warning('Starting job {}'.format(job_id))

            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE job SET status='Running', started = ? WHERE id = ?",
                (datetime.utcnow(), job_id)
            )
            self.db.commit()

            # self.add_blocking_task(self.run_job, job_id)
            self.add_task(self.run_job2(job_id, path))
            logger.warning('Submitted job {}'.format(job_id))

    async def run_job2(self, job_id, wdir):
        """Run the given job.

        Parameters
        ----------
        job_id : integer
            The id of the job to run.
        """
        logger.warning('Running job {}'.format(job_id))

        run_flowchart(job_id=job_id, wdir=wdir)

        logger.warning('Completed job {}'.format(job_id))

        return {
            'task': 'ran job',
            'job_id': job_id
        }  # yapf: disable

    async def run_job_in_thread(self, job_id):
        """Run the given job.

        Parameters
        ----------
        job_id : integer
            The id of the job to run.
        """
        logger.debug('Running job {} in a thread'.format(job_id))

        loop = asyncio.get_event_loop()
        # result = await loop.run_in_executor(
        #     None, functools.partial(run_job, job_id)
        # )
        tmp = []
        tmp.append(loop.run_in_executor(None, run_job, job_id))
        completed, pending = await asyncio.wait(tmp)
        for task in completed:
            result = task.result()

        logger.debug('Return from job {} in thread: {}'.format(job_id, result))

        return result
