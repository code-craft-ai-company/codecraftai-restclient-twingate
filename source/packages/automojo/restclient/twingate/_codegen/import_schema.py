"""
    .. module:: import_schema
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Maintainer-facing GraphQL introspection import script for
                   the Twingate Admin API schema.

    Run by hand against a real Twingate network when the upstream schema
    changes::

        python -m automojo.restclient.twingate._codegen.import_schema \\
            --network <slug> --token <api-token>

    See the "Codegen Decision" section of ``AGENTS.md`` — at the time of
    package authoring no live Twingate network was available, so the
    generated output under ``model/``, ``inputs/``, ``queries/`` and
    ``mutations/`` is hand-authored from the documented Twingate GraphQL
    surface. This script remains the mechanical re-sync path for a
    maintainer who does have a live network.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import argparse
import hashlib
import json
import os

from http import HTTPStatus
from typing import Any, Dict

import requests

from automojo.errors.exceptions import ConfigurationError


# The canonical GraphQL introspection query. Trimmed to the fields the
# emitter consumes.
INTROSPECTION_QUERY = (
    "query IntrospectionQuery {"
    " __schema {"
    " queryType { name } mutationType { name }"
    " types {"
    " kind name"
    " fields { name type { kind name ofType { kind name"
    " ofType { kind name } } } }"
    " enumValues { name }"
    " inputFields { name type { kind name ofType { kind name } } }"
    " } } }"
)


def _spec_directory() -> str:
    """
        Resolve the absolute path of the ``_spec`` directory.

        :returns: The ``_spec`` directory path.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    package_dir = os.path.dirname(here)
    rtnval = os.path.join(package_dir, "_spec")
    return rtnval


def introspect(*, network_slug: str, api_token: str,
               timeout_seconds: float = 30.0) -> Dict[str, Any]:
    """
        POST the canonical GraphQL introspection query to a live Twingate
        network and return the decoded ``__schema`` payload.

        :param network_slug: The Twingate network slug.
        :param api_token: The Twingate service-account API token.
        :param timeout_seconds: HTTP request timeout.

        :returns: The decoded GraphQL introspection response.

        :raises: :class:`ConfigurationError` when the upstream response is
            non-200 or carries GraphQL ``errors``.
    """
    endpoint = f"https://{network_slug}.twingate.com/api/graphql/v1"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "X-Network-Slug": network_slug,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {"query": INTROSPECTION_QUERY, "operationName": "IntrospectionQuery"}

    response = requests.post(
        endpoint, headers=headers, json=body, timeout=timeout_seconds)

    if response.status_code != HTTPStatus.OK:
        err_msg_lines = [
            "Twingate GraphQL introspection returned a non-200 status.",
            f"NETWORK SLUG: {network_slug}",
            f"STATUS: {response.status_code}",
            f"BODY: {response.text[:512]}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise ConfigurationError(err_msg)

    payload = response.json()

    errors = payload.get("errors")
    if errors is not None and len(errors) > 0:
        err_msg_lines = [
            "Twingate GraphQL introspection returned GraphQL errors.",
            f"NETWORK SLUG: {network_slug}",
            f"ERRORS: {errors}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise ConfigurationError(err_msg)

    rtnval = payload
    return rtnval


def save_schema(*, payload: Dict[str, Any]) -> str:
    """
        Save an introspection payload to ``_spec/schema.json`` and record
        its SHA-256 in ``_spec/schema.sha256``.

        :param payload: The introspection payload to persist.

        :returns: The computed SHA-256 hex digest.
    """
    spec_dir = _spec_directory()
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    schema_text = json.dumps(payload, indent=2, sort_keys=True)
    schema_bytes = schema_text.encode("utf-8")

    digest = hashlib.sha256(schema_bytes).hexdigest()

    schema_path = os.path.join(spec_dir, "schema.json")
    with open(schema_path, "w", encoding="utf-8") as schema_file:
        schema_file.write(schema_text)

    hash_path = os.path.join(spec_dir, "schema.sha256")
    with open(hash_path, "w", encoding="utf-8") as hash_file:
        hash_file.write(digest)

    rtnval = digest
    return rtnval


def main() -> int:
    """
        Command-line entry point for the introspection import script.

        :returns: Process exit code — ``0`` on success.
    """
    parser = argparse.ArgumentParser(
        description="Introspect a live Twingate network and dump the "
                    "GraphQL schema.")
    parser.add_argument(
        "--network", required=True, help="Twingate network slug.")
    parser.add_argument(
        "--token", required=True,
        help="Twingate service-account API token.")
    args = parser.parse_args()

    payload = introspect(network_slug=args.network, api_token=args.token)
    digest = save_schema(payload=payload)

    print(f"Twingate schema saved. SHA-256: {digest}")

    rtnval = 0
    return rtnval


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["INTROSPECTION_QUERY", "introspect", "save_schema", "main"]
