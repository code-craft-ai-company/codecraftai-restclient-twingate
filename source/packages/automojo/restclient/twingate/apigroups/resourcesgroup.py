"""
    .. module:: resourcesgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ResourcesGroup` api group
                   wrapping the Twingate ``resources`` GraphQL surface.

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
from automojo.restclient.twingate.acltranslator.intermediate import (
    IntermediateEdge
)
from automojo.restclient.twingate.exceptions import VPNControlPlaneQueryError
from automojo.restclient.twingate.model.twingateresource import TwingateResource
from automojo.restclient.twingate.queries.build_resources import build_resources
from automojo.restclient.twingate.queries.build_node import build_resource
from automojo.restclient.twingate.mutations.build_resource_mutations import (
    build_resourcecreate, build_resourceupdate, build_resourcedelete
)


def _resource_from_node(*, node: Dict[str, Any]) -> TwingateResource:
    """
        Project a GraphQL ``Resource`` node dictionary into a
        :class:`TwingateResource`.

        :param node: The GraphQL ``Resource`` node dictionary.

        :returns: A :class:`TwingateResource` instance.
    """
    address_block = node.get("address")
    address = ""
    if address_block is not None:
        address = address_block.get("value", "")

    remote_network = node.get("remoteNetwork")
    remote_network_id = ""
    if remote_network is not None:
        remote_network_id = remote_network.get("id", "")

    rtnval = TwingateResource(
        resource_id=node.get("id", ""),
        name=node.get("name", ""),
        address=address,
        remote_network_id=remote_network_id,
        protocols={},
    )
    return rtnval


class ResourcesGroup(RestApiGroup):
    """
        Api group wrapping the Twingate ``resources`` GraphQL surface —
        ``list``, ``iter``, ``get``, ``create``, ``update`` and ``delete``.

        Each method calls a typed builder from :mod:`queries` or
        :mod:`mutations`, POSTs through the owning :class:`TwingateClient`
        and projects the response into a :class:`TwingateResource`.
    """

    def list(self, *, after: Optional[str] = None,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[TwingateResource]:
        """
            List the first page of resources.

            :param after: Optional cursor token for the next page.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TwingateResource` records for one
                page.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_resources(after=after)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="resources")

        results = _extract_resource_page(data=data)[0]
        rtnval = results
        return rtnval

    def iter(self, *,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Iterator[TwingateResource]:
        """
            Iterate every resource across all pages using cursor-based
            paging.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TwingateResource` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        cursor: Optional[str] = None
        while True:
            request_body = build_resources(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(payload=payload, operation="resources")

            page_items, next_cursor = _extract_resource_page(data=data)
            for item in page_items:
                yield item

            if next_cursor is None:
                break
            cursor = next_cursor
        return

    def iter_assignments(self, *,
                         aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[IntermediateEdge]:
        """
            Read every resource-group assignment currently on the network
            as a list of :class:`IntermediateEdge` records.

            The ``resources`` query nests each resource's assigned groups;
            this method walks all pages and flattens the nesting into the
            provider-neutral edge shape the ACL differ consumes.

            :param aspects: Behaviour control for the call.

            :returns: A sorted list of :class:`IntermediateEdge` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        edge_set = set()

        cursor: Optional[str] = None
        while True:
            request_body = build_resources(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(payload=payload, operation="resources")

            resources_block = data.get("resources")
            if resources_block is None:
                break

            edges = resources_block.get("edges")
            if edges is None:
                edges = []

            for edge in edges:
                node = edge.get("node")
                if node is None:
                    continue
                resource_name = node.get("name", "")
                groups_block = node.get("groups")
                if groups_block is None:
                    continue
                group_edges = groups_block.get("edges")
                if group_edges is None:
                    group_edges = []
                for group_edge in group_edges:
                    group_node = group_edge.get("node")
                    if group_node is None:
                        continue
                    group_name = group_node.get("name", "")
                    edge_set.add(IntermediateEdge(
                        group_name=group_name,
                        resource_name=resource_name))

            next_cursor: Optional[str] = None
            page_info = resources_block.get("pageInfo")
            if page_info is not None:
                has_next = page_info.get("hasNextPage", False)
                if has_next is True:
                    next_cursor = page_info.get("endCursor")

            if next_cursor is None:
                break
            cursor = next_cursor

        results = sorted(
            edge_set, key=lambda e: (e.group_name, e.resource_name))
        rtnval = results
        return rtnval

    def get(self, *, resource_id: str,
            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Optional[TwingateResource]:
        """
            Fetch a single resource by identifier.

            :param resource_id: Provider-assigned resource identifier.
            :param aspects: Behaviour control for the call.

            :returns: The :class:`TwingateResource`, or ``None`` when no
                resource with the supplied identifier exists.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_resource(resource_id=resource_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="resource")

        node = data.get("resource")
        if node is None:
            rtnval: Optional[TwingateResource] = None
            return rtnval

        rtnval = _resource_from_node(node=node)
        return rtnval

    def create(self, *, name: str, address: str, remote_network_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateResource:
        """
            Create a resource.

            :param name: Resource display name.
            :param address: FQDN, IP, or CIDR.
            :param remote_network_id: Parent remote-network identifier.
            :param aspects: Behaviour control for the call.

            :returns: The newly created :class:`TwingateResource`.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_resourcecreate(
            name=name, address=address, remote_network_id=remote_network_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="resourceCreate", acl_phase=True)

        rtnval = _resource_from_entity(
            entity=result.get("entity"), fallback_address=address)
        return rtnval

    def update(self, *, resource_id: str, name: Optional[str] = None,
               address: Optional[str] = None,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateResource:
        """
            Update a resource.

            :param resource_id: Provider-assigned identifier.
            :param name: New display name, or ``None`` to leave unchanged.
            :param address: New address, or ``None`` to leave unchanged.
            :param aspects: Behaviour control for the call.

            :returns: The updated :class:`TwingateResource`.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_resourceupdate(
            resource_id=resource_id, name=name, address=address)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="resourceUpdate", acl_phase=True)

        fallback_address = ""
        if address is not None:
            fallback_address = address

        rtnval = _resource_from_entity(
            entity=result.get("entity"), fallback_address=fallback_address)
        return rtnval

    def delete(self, *, resource_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Delete a resource by identifier.

            :param resource_id: Provider-assigned identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_resourcedelete(resource_id=resource_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        require_mutation_result(
            payload=payload, mutation_name="resourceDelete", acl_phase=True)
        return None


def _resource_from_entity(*, entity: Optional[Dict[str, Any]],
                          fallback_address: str) -> TwingateResource:
    """
        Project a GraphQL mutation ``entity`` block into a
        :class:`TwingateResource`.

        :param entity: The mutation ``entity`` block, possibly ``None``.
        :param fallback_address: Address to use when the entity block does
            not echo an address (resource mutations may omit it).

        :returns: A :class:`TwingateResource` instance.

        :raises: :class:`VPNControlPlaneQueryError` when ``entity`` is
            ``None``.
    """
    if entity is None:
        err_msg_lines = [
            "Twingate resource mutation returned ok=True but no entity.",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneQueryError(err_msg)

    address_block = entity.get("address")
    address = fallback_address
    if address_block is not None:
        address = address_block.get("value", fallback_address)

    remote_network = entity.get("remoteNetwork")
    remote_network_id = ""
    if remote_network is not None:
        remote_network_id = remote_network.get("id", "")

    rtnval = TwingateResource(
        resource_id=entity.get("id", ""),
        name=entity.get("name", ""),
        address=address,
        remote_network_id=remote_network_id,
        protocols={},
    )
    return rtnval


def _extract_resource_page(*, data: Dict[str, Any]) -> tuple:
    """
        Extract one page of resources and the next cursor from a
        ``resources`` query ``data`` block.

        :param data: The ``data`` block from a ``resources`` query.

        :returns: A two-tuple ``(items, next_cursor)`` where ``items`` is a
            list of :class:`TwingateResource` and ``next_cursor`` is the
            cursor token for the next page or ``None``.
    """
    resources_block = data.get("resources")
    if resources_block is None:
        rtnval = ([], None)
        return rtnval

    edges = resources_block.get("edges")
    if edges is None:
        edges = []

    results: List[TwingateResource] = []
    for edge in edges:
        node = edge.get("node")
        if node is None:
            continue
        results.append(_resource_from_node(node=node))

    next_cursor: Optional[str] = None
    page_info = resources_block.get("pageInfo")
    if page_info is not None:
        has_next = page_info.get("hasNextPage", False)
        if has_next is True:
            next_cursor = page_info.get("endCursor")

    rtnval = (results, next_cursor)
    return rtnval


__all__ = ["ResourcesGroup"]
