# -*- coding: utf-8 -*-

"""
seamm_jobserver
JobServer for the SEAMM environment.
"""

# Bring up the classes so that they appear to be directly in
# the seamm_jobserver package.

from seamm_jobserver.jobserver import JobServer  # noqa: F401

# Handle versioneer
from ._version import get_versions  # noqa: E402

__author__ = """Paul Saxe"""
__email__ = "psaxe@molssi.org"
versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
