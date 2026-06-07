"""
    .. module:: groupsgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`GroupsGroup` api group
                   wrapping the Twingate ``groups`` GraphQL surface.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Any, Dict, Iterator, List, Optional

from ccai.restclient.base.restapigroup import RestApiGroup

from ccai.restclient.twingate.aspectstwingate import (
    AspectsTwingate, DEFAULT_TWINGATE_ASPECTS
)
from ccai.restclient.twingate.apigroups.graphqlsupport import (
    require_query_data, require_mutation_result
)
from ccai.restclient.twingate.exceptions import VPNControlPlaneQueryError
from ccai.restclient.twingate.model.twingategroup import TwingateGroup
from ccai.restclient.twingate.queries.build_groups import build_groups
from ccai.restclient.twingate.queries.build_node import build_group
from ccai.restclient.twingate.mutations.build_group_mutations import (
    build_groupcreate, build_groupupdate, build_groupdelete
)


def _group_from_node(*, node: Dict[str, Any]) -> TwingateGroup:
    """
        Project a GraphQL ``Group`` node dictionary into a
        :class:`TwingateGroup`.

        :param node: The GraphQL ``Group`` node dictionary.

        :returns: A :class:`TwingateGroup` instance.
    """
    rtnval = TwingateGroup(
        group_id=node.get("id", ""),
        name=node.get("name", ""),
        user_ids=[],
    )
    return rtnval


class GroupsGroup(RestApiGroup):
    """
        Api group wrapping the Twingate ``groups`` GraphQL surface —
        ``list``, ``iter``, ``get``, ``create``, ``update`` and ``delete``.
    """

    def list(self, *, after: Optional[str] = None,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[TwingateGroup]:
        """
            List the first page of groups.

            :param after: Optional cursor token for the next page.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TwingateGroup` records for one page.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_groups(after=after)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="groups")

        results = _extract_group_page(data=data)[0]
        rtnval = results
        return rtnval

    def iter(self, *,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Iterator[TwingateGroup]:
        """
            Iterate every group across all pages using cursor-based paging.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TwingateGroup` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        cursor: Optional[str] = None
        while True:
            request_body = build_groups(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(payload=payload, operation="groups")

            page_items, next_cursor = _extract_group_page(data=data)
            for item in page_items:
                yield item

            if next_cursor is None:
                break
            cursor = next_cursor
        return

    def get(self, *, group_id: str,
            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Optional[TwingateGroup]:
        """
            Fetch a single group by identifier.

            :param group_id: Provider-assigned group identifier.
            :param aspects: Behaviour control for the call.

            :returns: The :class:`TwingateGroup`, or ``None`` when no group
                with the supplied identifier exists.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_group(group_id=group_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="group")

        node = data.get("group")
        if node is None:
            rtnval: Optional[TwingateGroup] = None
            return rtnval

        rtnval = _group_from_node(node=node)
        return rtnval

    def create(self, *, name: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateGroup:
        """
            Create a group.

            :param name: Group display name.
            :param aspects: Behaviour control for the call.

            :returns: The newly created :class:`TwingateGroup`.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_groupcreate(name=name)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="groupCreate", acl_phase=True)

        rtnval = _group_from_entity(entity=result.get("entity"))
        return rtnval

    def update(self, *, group_id: str, name: Optional[str] = None,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> TwingateGroup:
        """
            Update a group.

            :param group_id: Provider-assigned identifier.
            :param name: New display name, or ``None`` to leave unchanged.
            :param aspects: Behaviour control for the call.

            :returns: The updated :class:`TwingateGroup`.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_groupupdate(group_id=group_id, name=name)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        result = require_mutation_result(
            payload=payload, mutation_name="groupUpdate", acl_phase=True)

        rtnval = _group_from_entity(entity=result.get("entity"))
        return rtnval

    def delete(self, *, group_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Delete a group by identifier.

            :param group_id: Provider-assigned identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_groupdelete(group_id=group_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        require_mutation_result(
            payload=payload, mutation_name="groupDelete", acl_phase=True)
        return None


def _group_from_entity(*, entity: Optional[Dict[str, Any]]) -> TwingateGroup:
    """
        Project a GraphQL mutation ``entity`` block into a
        :class:`TwingateGroup`.

        :param entity: The mutation ``entity`` block, possibly ``None``.

        :returns: A :class:`TwingateGroup` instance.

        :raises: :class:`VPNControlPlaneQueryError` when ``entity`` is
            ``None``.
    """
    if entity is None:
        err_msg_lines = [
            "Twingate group mutation returned ok=True but no entity.",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneQueryError(err_msg)

    rtnval = TwingateGroup(
        group_id=entity.get("id", ""),
        name=entity.get("name", ""),
        user_ids=[],
    )
    return rtnval


def _extract_group_page(*, data: Dict[str, Any]) -> tuple:
    """
        Extract one page of groups and the next cursor from a ``groups``
        query ``data`` block.

        :param data: The ``data`` block from a ``groups`` query.

        :returns: A two-tuple ``(items, next_cursor)``.
    """
    groups_block = data.get("groups")
    if groups_block is None:
        rtnval = ([], None)
        return rtnval

    edges = groups_block.get("edges")
    if edges is None:
        edges = []

    results: List[TwingateGroup] = []
    for edge in edges:
        node = edge.get("node")
        if node is None:
            continue
        results.append(_group_from_node(node=node))

    next_cursor: Optional[str] = None
    page_info = groups_block.get("pageInfo")
    if page_info is not None:
        has_next = page_info.get("hasNextPage", False)
        if has_next is True:
            next_cursor = page_info.get("endCursor")

    rtnval = (results, next_cursor)
    return rtnval


__all__ = ["GroupsGroup"]
