"""
    .. module:: exceptions
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed exception hierarchy raised
                   by the Twingate GraphQL client.

    The ``automojo-restclient-twingate`` package is a standalone vendor REST
    client. It does not couple to ``automojo-interop``; the GraphQL-specific
    failure types live here.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional


class TwingateClientError(Exception):
    """
        Base class for every error raised by the Twingate GraphQL client.
    """


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
    "VPNControlPlaneQueryError",
    "VPNControlPlaneMutationError",
    "VPNControlPlaneAuthKeyError",
    "VPNControlPlaneACLError",
]
