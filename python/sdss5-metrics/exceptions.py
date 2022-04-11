# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32

from __future__ import print_function, division, absolute_import


class Sdss5-metricsError(Exception):
    """A custom core Sdss5-metrics exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(Sdss5-metricsError, self).__init__(message)


class Sdss5-metricsNotImplemented(Sdss5-metricsError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(Sdss5-metricsNotImplemented, self).__init__(message)


class Sdss5-metricsAPIError(Sdss5-metricsError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from Sdss5-metrics API'
        else:
            message = 'Http response error from Sdss5-metrics API. {0}'.format(message)

        super(Sdss5-metricsAPIError, self).__init__(message)


class Sdss5-metricsApiAuthError(Sdss5-metricsAPIError):
    """A custom exception for API authentication errors"""
    pass


class Sdss5-metricsMissingDependency(Sdss5-metricsError):
    """A custom exception for missing dependencies."""
    pass


class Sdss5-metricsWarning(Warning):
    """Base warning for Sdss5-metrics."""


class Sdss5-metricsUserWarning(UserWarning, Sdss5-metricsWarning):
    """The primary warning class."""
    pass


class Sdss5-metricsSkippedTestWarning(Sdss5-metricsUserWarning):
    """A warning for when a test is skipped."""
    pass


class Sdss5-metricsDeprecationWarning(Sdss5-metricsUserWarning):
    """A warning for deprecated features."""
    pass
