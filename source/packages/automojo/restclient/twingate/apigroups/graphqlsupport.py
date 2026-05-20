"""
    .. module:: graphqlsupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains shared GraphQL response inspection
                   helpers used by the Twingate api groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Dict, List

from automojo.restclient.twingate.exceptions import (
    VPNControlPlaneACLError,
    VPNControlPlaneMutationError,
    VPNControlPlaneQueryError,
)


def require_query_data(*, payload: Dict[str, Any],
                       operation: str) -> Dict[str, Any]:
    """
        Validate a GraphQL query response and return its ``data`` block.

        :param payload: The decoded GraphQL response.
        :param operation: The query operation name, for error context.

        :returns: The ``data`` block from the payload.

        :raises: :class:`VPNControlPlaneQueryError` when the payload
            carries top-level GraphQL errors or has no ``data`` block.
    """
    errors = payload.get("errors")
    if errors is not None and len(errors) > 0:
        err_msg_lines = [
            f"Twingate '{operation}' query returned top-level GraphQL errors.",
            f"ERRORS: {errors}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneQueryError(err_msg, response_body=str(payload))

    data = payload.get("data")
    if data is None:
        err_msg_lines = [
            f"Twingate '{operation}' query returned no 'data' payload.",
            f"PAYLOAD: {payload}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneQueryError(err_msg, response_body=str(payload))

    rtnval = data
    return rtnval


def require_mutation_result(*, payload: Dict[str, Any],
                            mutation_name: str,
                            acl_phase: bool = False) -> Dict[str, Any]:
    """
        Validate a GraphQL mutation response and return its result object.

        :param payload: The decoded GraphQL response.
        :param mutation_name: The mutation field name to read from ``data``.
        :param acl_phase: When ``True`` failures raise
            :class:`VPNControlPlaneACLError`; otherwise they raise
            :class:`VPNControlPlaneMutationError`.

        :returns: The mutation result object (containing ``ok`` /
            ``error`` / ``entity``).

        :raises: :class:`VPNControlPlaneACLError` or
            :class:`VPNControlPlaneMutationError`.
    """
    if acl_phase:
        error_type = VPNControlPlaneACLError
    else:
        error_type = VPNControlPlaneMutationError

    errors = payload.get("errors")
    if errors is not None and len(errors) > 0:
        err_msg_lines = [
            f"Twingate {mutation_name} returned top-level GraphQL errors.",
            f"ERRORS: {errors}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise error_type(err_msg, response_body=str(payload))

    data = payload.get("data")
    if data is None:
        err_msg_lines = [
            f"Twingate {mutation_name} returned no 'data' payload.",
            f"PAYLOAD: {payload}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise error_type(err_msg, response_body=str(payload))

    result = data.get(mutation_name)
    if result is None:
        err_msg_lines = [
            f"Twingate {mutation_name} returned no result object.",
            f"PAYLOAD: {payload}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise error_type(err_msg, response_body=str(payload))

    ok_flag = result.get("ok")
    if ok_flag is not True:
        err_msg_lines = [
            f"Twingate {mutation_name} reported ok=False.",
            f"ERROR: {result.get('error')}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise error_type(err_msg, response_body=str(payload))

    rtnval = result
    return rtnval


def errors_indicate_not_found(*, errors: List[Dict[str, Any]]) -> bool:
    """
        Inspect a GraphQL top-level ``errors`` list and report whether at
        least one entry indicates a not-found condition.

        :param errors: The list of error dictionaries.

        :returns: ``True`` when a not-found marker is present.
    """
    indicates_not_found = False
    for entry in errors:
        message = entry.get("message", "")
        if is_not_found_text(text=message):
            indicates_not_found = True
            break
    rtnval = indicates_not_found
    return rtnval


def is_not_found_text(*, text: str) -> bool:
    """
        Report whether ``text`` indicates a not-found condition.

        :param text: The error text to inspect.

        :returns: ``True`` when the text is recognised as a not-found
            marker.
    """
    if text is None:
        rtnval = False
        return rtnval

    lowered = text.lower()
    rtnval = False
    if "not found" in lowered:
        rtnval = True
    elif "does not exist" in lowered:
        rtnval = True

    return rtnval


__all__ = [
    "require_query_data",
    "require_mutation_result",
    "errors_indicate_not_found",
    "is_not_found_text",
]
