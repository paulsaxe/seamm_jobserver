=======
History
=======

2023.3.23 -- Substantial improvements to JobServer
   * Switched to independent process for Jobs, which means they are fully independent of
     the JobServer and continue to run if the JobServer stops
   * Discover existing running jobs on startup and monitor them.
   * Added status information for the machine the JobServer is on as well as Jobs
   * Provide a GUI if run from the commandline, showing the log and status.

0.9.1 (2020-05-29)
------------------

* First release on PyPI.
