"""
    .. module:: remotenetworksgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`RemoteNetworksGroup` api
                   group wrapping the Twingate ``remoteNetworks`` GraphQL
                   surface.

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
    require_query_data, require_mutation_result
)
from automojo.restclient.twingate.exceptions import VPNControlPlaneQueryError
from automojo.restclient.twingate.model.twingateremotenetwork import (
    TwingateRemoteNetwork
)
from automojo.restclient.twingate.queries.build_remotenetworks import (
    build_remotenetworks
)
from automojo.restclient.twingate.queries.build_node import build_remotenetwork
from automojo.restclient.twingate.mutations.build_remotenetwork_mutations import (
    build_remotenetworkcreate, build_remotenetworkupdate,
    build_remotenetworkdelete
)


def _remotenetwork_from_node(*, node: Dict[str, Any]) -> TwingateRemoteNetwork:
    """
        Project a GraphQL ``RemoteNetwork`` node dictionary into a
        :class:`TwingateRemoteNetwork`.

        :param node: The GraphQL ``RemoteNetwork`` node dictionary.

        :returns: A :class:`TwingateRemoteNetwork` instance.
    """
    rtnval = TwingateRemoteNetwork(
        remote_network_id=node.get("id", ""),
        name=node.get("name", ""),
        location=node.get("location", "") or "",
    )
    return rtnval


class RemoteNetworksGroup(RestApiGroup):
    """
        Api group wrapping the Twingate ``remoteNetworks`` GraphQL surface —
        ``list``, ``iter``, ``get``, ``create``, ``update`` and ``delete``.
    """

    def list(self, *, after: Optional[str] = None,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[TwingateRemoteNetwork]:
        """
            List the first page of remote networks.

            :param after: Optional cursor token for the next page.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TwingateRemoteNetwork` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_remotenetworks(after=after)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="remoteNetworks")

        results = _extract_remotenetwork_page(data=data)[0]
        rtnval = results
        return rtnval

    def iter(self, *,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Iterator[TwingateRemoteNetwork]:
        """
            Iterate every remote network across all pages using
            cursor-based paging.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TwingateRemoteNetwork`
                records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        cursor: Optional[str] = None
        while True:
            request_body = build_remotenetworks(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(
                payload=payload, operation="remoteNetworks")

            page_items, next_cursor = _extract_remotenetwork_page(data=data)
            for item in page_items:
                yield item

            if next_cursor is None:
                break
            cursor = next_cursor
        return

    def get(self, *, remote_network_id: str,
            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Optional[TwingateRemoteNetwork]:
        """
            Fetch a single remote network by identifier.

            :param remote_network_id: Provider-assigned identifier.
            :param aspects: Behaviour control for the call.

            :returns: The :class:`TwingateRemoteNetwork`, or ``None`` when
                no remote network with the supplied identifier exists.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_remotenetwork(remote_network_id=remote_network_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="remoteNetwork")

        node = data.get("remoteNetwork")
        if node is None:
            rtnval: Optional[TwingateRemoteNetwork] = None
            return rtnval

        rtnval = _remotenetwork_from_node(node=node)
        return rtnval

    def create(self, *, name: str, location: Optional[str] = None,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateRemoteNetwork:
        """
            Create a remote network.

            :param name: Remote-network display name.
            :param location: Optional location token.
            :param aspects: Behaviour control for the call.

            :returns: The newly created :class:`TwingateRemoteNetwork`.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        request_body = build_remotenetworkcreate(name=name, location=location)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="remoteNetworkCreate")

        rtnval = _remotenetwork_from_entity(entity=result.get("entity"))
        return rtnval

    def update(self, *, remote_network_id: str, name: Optional[str] = None,
               location: Optional[str] = None,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateRemoteNetwork:
        """
            Update a remote network.

            :param remote_network_id: Provider-assigned identifier.
            :param name: New display name, or ``None`` to leave unchanged.
            :param location: New location token, or ``None`` to leave
                unchanged.
            :param aspects: Behaviour control for the call.

            :returns: The updated :class:`TwingateRemoteNetwork`.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        request_body = build_remotenetworkupdate(
            remote_network_id=remote_network_id, name=name, location=location)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="remoteNetworkUpdate")

        rtnval = _remotenetwork_from_entity(entity=result.get("entity"))
        return rtnval

    def delete(self, *, remote_network_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Delete a remote network by identifier.

            :param remote_network_id: Provider-assigned identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        request_body = build_remotenetworkdelete(
            remote_network_id=remote_network_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        require_mutation_result(
            payload=payload, mutation_name="remoteNetworkDelete")
        return None


def _remotenetwork_from_entity(*,
                               entity: Optional[Dict[str, Any]]) -> TwingateRemoteNetwork:
    """
        Project a GraphQL mutation ``entity`` block into a
        :class:`TwingateRemoteNetwork`.

        :param entity: The mutation ``entity`` block, possibly ``None``.

        :returns: A :class:`TwingateRemoteNetwork` instance.

        :raises: :class:`VPNControlPlaneQueryError` when ``entity`` is
            ``None``.
    """
    if entity is None:
        err_msg_lines = [
            "Twingate remoteNetwork mutation returned ok=True but no entity.",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneQueryError(err_msg)

    rtnval = _remotenetwork_from_node(node=entity)
    return rtnval


def _extract_remotenetwork_page(*, data: Dict[str, Any]) -> tuple:
    """
        Extract one page of remote networks and the next cursor from a
        ``remoteNetworks`` query ``data`` block.

        :param data: The ``data`` block from a ``remoteNetworks`` query.

        :returns: A two-tuple ``(items, next_cursor)``.
    """
    block = data.get("remoteNetworks")
    if block is None:
        rtnval = ([], None)
        return rtnval

    edges = block.get("edges")
    if edges is None:
        edges = []

    results: List[TwingateRemoteNetwork] = []
    for edge in edges:
        node = edge.get("node")
        if node is None:
            continue
        results.append(_remotenetwork_from_node(node=node))

    next_cursor: Optional[str] = None
    page_info = block.get("pageInfo")
    if page_info is not None:
        has_next = page_info.get("hasNextPage", False)
        if has_next is True:
            next_cursor = page_info.get("endCursor")

    rtnval = (results, next_cursor)
    return rtnval


__all__ = ["RemoteNetworksGroup"]
