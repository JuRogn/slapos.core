# -*- coding: utf-8 -*-

"""
Provides helper functions to check if two binary caches are compatible.

os_matches(...):
    returns True if the arguments reference compatible platforms.

patched_linux_distribution(...):
    a patched version of platform.linux_distribution()

    this is the same function provided with the python package in Debian and Ubuntu:
        see http://bugs.python.org/issue9514

    otherwise, Ubuntu will always be reported as an unstable Debian, regardless of the version.
"""

import platform
import re


def _debianize(os):
    """
    keep only the major release number in case of debian, otherwise
    minor releases would be seen as not compatible to each other.
    """
    distname, version, id_ = os
    if distname == 'debian' and '.' in version:
        version = version.split('.')[0]
    return distname, version, id_


def os_matches(os1, os2):
    return _debianize(os1) == _debianize(os2)


_distributor_id_file_re = re.compile("(?:DISTRIB_ID\s*=)\s*(.*)", re.I)
_release_file_re = re.compile("(?:DISTRIB_RELEASE\s*=)\s*(.*)", re.I)
_codename_file_re = re.compile("(?:DISTRIB_CODENAME\s*=)\s*(.*)", re.I)


def patched_linux_distribution(distname='', version='', id='',
                               supported_dists=platform._supported_dists,
                               full_distribution_name=1):
    # check for the Debian/Ubuntu /etc/lsb-release file first, needed so
    # that the distribution doesn't get identified as Debian.
    try:
        etclsbrel = open("/etc/lsb-release", "rU")
        for line in etclsbrel:
            m = _distributor_id_file_re.search(line)
            if m:
                _u_distname = m.group(1).strip()
            m = _release_file_re.search(line)
            if m:
                _u_version = m.group(1).strip()
            m = _codename_file_re.search(line)
            if m:
                _u_id = m.group(1).strip()
        if _u_distname and _u_version:
            return (_u_distname, _u_version, _u_id)
    except (EnvironmentError, UnboundLocalError):
            pass

    return platform.linux_distribution(distname, version, id, supported_dists, full_distribution_name)
