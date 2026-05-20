"""
    .. module:: connectorsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ConnectorsGroup` api group
                   wrapping the Twingate ``connectors`` GraphQL surface.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Dict, Iterator, List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.twingate.aspectstwingate import (
    AspectsTwingate, DEFAULT_TWINGATE_ASPECTS
)
from automojo.restclient.twingate.apigroups.graphqlsupport import (
    require_query_data, require_mutation_result, errors_indicate_not_found,
    is_not_found_text
)
from automojo.restclient.twingate.exceptions import (
    VPNControlPlaneAuthKeyError, VPNControlPlaneMutationError
)
from automojo.restclient.twingate.model.twingateconnector import TwingateConnector
from automojo.restclient.twingate.queries.build_connectors import build_connectors
from automojo.restclient.twingate.queries.build_node import build_connector
from automojo.restclient.twingate.mutations.build_connector_mutations import (
    build_connectorcreate, build_connectorgeneratetokens, build_connectordelete
)


def _connector_from_node(*, node: Dict[str, Any]) -> TwingateConnector:
    """
        Project a GraphQL ``Connector`` node dictionary into a
        :class:`TwingateConnector`.

        :param node: The GraphQL ``Connector`` node dictionary.

        :returns: A :class:`TwingateConnector` instance.
    """
    remote_network = node.get("remoteNetwork")
    remote_network_id = ""
    if remote_network is not None:
        remote_network_id = remote_network.get("id", "")

    rtnval = TwingateConnector(
        connector_id=node.get("id", ""),
        name=node.get("name", ""),
        remote_network_id=remote_network_id,
        state=node.get("state", ""),
    )
    return rtnval


class ConnectorsGroup(RestApiGroup):
    """
        Api group wrapping the Twingate ``connectors`` GraphQL surface —
        ``list``, ``iter``, ``get``, ``create``, ``generate_tokens`` and
        ``delete``.
    """

    def list(self, *, after: Optional[str] = None,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[TwingateConnector]:
        """
            List the first page of connectors.

            :param after: Optional cursor token for the next page.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TwingateConnector` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_connectors(after=after)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="connectors")

        results = _extract_connector_page(data=data)[0]
        rtnval = results
        return rtnval

    def iter(self, *,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Iterator[TwingateConnector]:
        """
            Iterate every connector across all pages using cursor-based
            paging.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TwingateConnector` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        cursor: Optional[str] = None
        while True:
            request_body = build_connectors(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(
                payload=payload, operation="connectors")

            page_items, next_cursor = _extract_connector_page(data=data)
            for item in page_items:
                yield item

            if next_cursor is None:
                break
            cursor = next_cursor
        return

    def get(self, *, connector_id: str,
            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Optional[TwingateConnector]:
        """
            Fetch a single connector by identifier.

            :param connector_id: Provider-assigned connector identifier.
            :param aspects: Behaviour control for the call.

            :returns: The :class:`TwingateConnector`, or ``None`` when no
                connector with the supplied identifier exists.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_connector(connector_id=connector_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="connector")

        node = data.get("connector")
        if node is None:
            rtnval: Optional[TwingateConnector] = None
            return rtnval

        rtnval = _connector_from_node(node=node)
        return rtnval

    def create(self, *, remote_network_id: str, name: Optional[str] = None,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateConnector:
        """
            Create a connector inside a remote network.

            :param remote_network_id: Parent remote-network identifier.
            :param name: Optional connector display name.
            :param aspects: Behaviour control for the call.

            :returns: The newly created :class:`TwingateConnector`.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        request_body = build_connectorcreate(
            remote_network_id=remote_network_id, name=name)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="connectorCreate")

        entity = result.get("entity")
        if entity is None:
            err_msg_lines = [
                "Twingate connectorCreate returned ok=True but no entity.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(err_msg)

        rtnval = _connector_from_node(node=entity)
        return rtnval

    def generate_tokens(self, *, connector_id: str,
                        aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Dict[str, str]:
        """
            Issue the ``connectorGenerateTokens`` mutation against the
            target connector.

            :param connector_id: Provider-assigned connector identifier.
            :param aspects: Behaviour control for the call.

            :returns: A dictionary with ``access_token`` and
                ``refresh_token`` keys.

            :raises: :class:`VPNControlPlaneAuthKeyError`.
        """
        if connector_id is None or len(connector_id) == 0:
            err_msg_lines = [
                "ConnectorsGroup.generate_tokens requires a non-empty "
                "'connector_id'.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(err_msg)

        request_body = build_connectorgeneratetokens(connector_id=connector_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)

        errors = payload.get("errors")
        if errors is not None and len(errors) > 0:
            err_msg_lines = [
                "Twingate connectorGenerateTokens returned top-level errors.",
                f"CONNECTOR_ID: {connector_id}",
                f"ERRORS: {errors}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(
                err_msg, response_body=str(payload))

        data = payload.get("data")
        if data is None:
            err_msg_lines = [
                "Twingate connectorGenerateTokens returned no 'data'.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(
                err_msg, response_body=str(payload))

        result = data.get("connectorGenerateTokens")
        if result is None or result.get("ok") is not True:
            err_msg_lines = [
                "Twingate connectorGenerateTokens did not succeed.",
                f"CONNECTOR_ID: {connector_id}",
                f"RESULT: {result}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(
                err_msg, response_body=str(payload))

        tokens = result.get("connectorTokens")
        if tokens is None:
            err_msg_lines = [
                "Twingate connectorGenerateTokens returned ok=True but no "
                "tokens.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(
                err_msg, response_body=str(payload))

        access_token = tokens.get("accessToken")
        refresh_token = tokens.get("refreshToken")
        if access_token is None or refresh_token is None:
            err_msg_lines = [
                "Twingate connectorGenerateTokens returned an incomplete "
                "token pair.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(
                err_msg, response_body=str(payload))

        rtnval = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        return rtnval

    def delete(self, *, connector_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Delete a connector by identifier. Treats a not-found result as
            success so the call is idempotent.

            :param connector_id: Provider-assigned connector identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        if connector_id is None or len(connector_id) == 0:
            err_msg_lines = [
                "ConnectorsGroup.delete requires a non-empty 'connector_id'.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(err_msg)

        request_body = build_connectordelete(connector_id=connector_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)

        errors = payload.get("errors")
        if errors is not None and len(errors) > 0:
            if errors_indicate_not_found(errors=errors):
                return None
            err_msg_lines = [
                "Twingate connectorDelete returned top-level GraphQL errors.",
                f"CONNECTOR_ID: {connector_id}",
                f"ERRORS: {errors}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        data = payload.get("data")
        if data is None:
            err_msg_lines = [
                "Twingate connectorDelete returned no 'data' payload.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        result = data.get("connectorDelete")
        if result is None:
            err_msg_lines = [
                "Twingate connectorDelete returned no result object.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        if result.get("ok") is True:
            return None

        error_text = result.get("error")
        if error_text is not None and is_not_found_text(text=error_text):
            return None

        err_msg_lines = [
            "Twingate connectorDelete reported ok=False.",
            f"CONNECTOR_ID: {connector_id}",
            f"ERROR: {error_text}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneMutationError(err_msg, response_body=str(payload))


def _extract_connector_page(*, data: Dict[str, Any]) -> tuple:
    """
        Extract one page of connectors and the next cursor from a
        ``connectors`` query ``data`` block.

        :param data: The ``data`` block from a ``connectors`` query.

        :returns: A two-tuple ``(items, next_cursor)``.
    """
    connectors_block = data.get("connectors")
    if connectors_block is None:
        rtnval = ([], None)
        return rtnval

    edges = connectors_block.get("edges")
    if edges is None:
        edges = []

    results: List[TwingateConnector] = []
    for edge in edges:
        node = edge.get("node")
        if node is None:
            continue
        results.append(_connector_from_node(node=node))

    next_cursor: Optional[str] = None
    page_info = connectors_block.get("pageInfo")
    if page_info is not None:
        has_next = page_info.get("hasNextPage", False)
        if has_next is True:
            next_cursor = page_info.get("endCursor")

    rtnval = (results, next_cursor)
    return rtnval


__all__ = ["ConnectorsGroup"]
