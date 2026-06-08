"""
    .. module:: exceptions
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed exception hierarchy raised
                   by the Twingate GraphQL client.

    The ``codecraftai-restclient-twingate`` package is a standalone vendor REST
    client. It does not couple to ``codecraftai-interop``; the GraphQL-specific
    failure types live here.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Optional


class TwingateClientError(Exception):
    """
        Base class for every error raised by the Twingate GraphQL client.
    """


class TwingateApiError(TwingateClientError):
    """
        Base class for every error raised when the Twingate API returns a
        non-2xx HTTP response. The originating status code and response body
        are preserved so callers may inspect them directly.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        """
            Initialize the API error with HTTP response context.

            :param message: A descriptive, multi-line error message.
            :param status_code: The HTTP status code returned by the API.
            :param response_body: The raw response body text from the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        return


class TwingateAuthError(TwingateApiError):
    """
        Raised when the Twingate API rejects a request with a ``401`` or
        ``403`` status — the service-account token is missing, invalid, or
        lacks the scope required for the attempted action.
    """


class TwingateNotFoundError(TwingateApiError):
    """
        Raised when the Twingate API returns a ``404`` status — the
        addressed endpoint or resource does not exist.
    """


class TwingateRateLimitError(TwingateApiError):
    """
        Raised when the Twingate API returns a ``429`` status — the caller
        has exceeded the upstream request-rate budget.
    """


class TwingateServerError(TwingateApiError):
    """
        Raised when the Twingate API returns a ``5xx`` status — the upstream
        service failed to process an otherwise well-formed request.
    """


def classify_http_status(*, status_code: int, operation: str,
                          response_body: str) -> TwingateApiError:
    """
        Map a non-2xx HTTP status code onto the most specific
        :class:`TwingateApiError` subclass and build it with descriptive,
        multi-line context.

        :param status_code: The HTTP status code returned by the API.
        :param operation: The GraphQL operation name, for error context.
        :param response_body: The raw response body text from the API.

        :returns: A :class:`TwingateApiError` (or subclass) instance ready
            to be raised by the caller.
    """
    if status_code in (401, 403):
        error_type = TwingateAuthError
    elif status_code == 404:
        error_type = TwingateNotFoundError
    elif status_code == 429:
        error_type = TwingateRateLimitError
    elif 500 <= status_code < 600:
        error_type = TwingateServerError
    else:
        error_type = TwingateApiError

    err_msg_lines = [
        "Twingate API call failed: {}.".format(operation),
    ]
    err_msg_lines.append("STATUS: {}".format(status_code))
    err_msg_lines.append("RESPONSE:")
    err_msg_lines.append(response_body)
    err_msg = os.linesep.join(err_msg_lines)

    rtnval = error_type(err_msg, status_code=status_code,
                        response_body=response_body)
    return rtnval


class VPNControlPlaneQueryError(TwingateClientError):
    """
        Raised when a Twingate GraphQL query returns top-level ``errors``
        or an undecodable payload.
    """

    def __init__(self, message: str, response_body: Optional[str] = None,
                 status_code: Optional[int] = None):
        """
            Initialize the query error with response context.

            :param message: A descriptive error message.
            :param response_body: The raw response body text from the API.
            :param status_code: The HTTP status code returned by the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.response_body = response_body
        self.status_code = status_code
        return


class VPNControlPlaneMutationError(TwingateClientError):
    """
        Raised when a Twingate GraphQL mutation fails with top-level
        ``errors`` or an ``ok=False`` payload.
    """

    def __init__(self, message: str, response_body: Optional[str] = None,
                 status_code: Optional[int] = None):
        """
            Initialize the mutation error with response context.

            :param message: A descriptive error message.
            :param response_body: The raw response body text from the API.
            :param status_code: The HTTP status code returned by the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.response_body = response_body
        self.status_code = status_code
        return


class VPNControlPlaneAuthKeyError(TwingateClientError):
    """
        Raised when minting a Twingate connector token fails — either the
        connector name does not resolve or the mutation returns errors.
    """

    def __init__(self, message: str, request_body: Optional[dict] = None,
                 response_body: Optional[str] = None,
                 status_code: Optional[int] = None):
        """
            Initialize the auth-key error with request and response
            context.

            :param message: A descriptive error message.
            :param request_body: The dictionary sent as the POST body.
            :param response_body: The raw response body text from the API.
            :param status_code: The HTTP status code returned by the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.request_body = request_body
        self.response_body = response_body
        self.status_code = status_code
        return


class VPNControlPlaneACLError(TwingateClientError):
    """
        Raised when a phase of the three-phase :meth:`apply_acl` translation
        fails against the Twingate API.
    """

    def __init__(self, message: str, response_body: Optional[str] = None,
                 status_code: Optional[int] = None):
        """
            Initialize the ACL error with response context.

            :param message: A descriptive error message.
            :param response_body: The raw response body text from the API.
            :param status_code: The HTTP status code returned by the API.

            :returns: ``None``.
        """
        super().__init__(message)
        self.response_body = response_body
        self.status_code = status_code
        return


__all__ = [
    "TwingateClientError",
    "TwingateApiError",
    "TwingateAuthError",
    "TwingateNotFoundError",
    "TwingateRateLimitError",
    "TwingateServerError",
    "classify_http_status",
    "VPNControlPlaneQueryError",
    "VPNControlPlaneMutationError",
    "VPNControlPlaneAuthKeyError",
    "VPNControlPlaneACLError",
]
