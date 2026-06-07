"""
    .. module:: build_group_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builders
                   for the Twingate group lifecycle mutations
                   (``groupCreate``, ``groupUpdate``, ``groupDelete``).

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.
    DO NOT EDIT BY HAND once GraphQL introspection codegen is live; regenerate
    via ``python -m ccai.restclient.twingate._codegen.import_schema``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional

from ccai.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from ccai.restclient.twingate.queries.buildersupport import build_variables


GROUP_CREATE_MUTATION = (
    "mutation GroupCreate($name: String!) {"
    " groupCreate(name: $name) { ok error entity { id name } }"
    " }"
)

GROUP_UPDATE_MUTATION = (
    "mutation GroupUpdate($id: ID!, $name: String) {"
    " groupUpdate(id: $id, name: $name) { ok error entity { id name } }"
    " }"
)

GROUP_DELETE_MUTATION = (
    "mutation GroupDelete($id: ID!) {"
    " groupDelete(id: $id) { ok error }"
    " }"
)


def build_groupcreate(*, name: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``groupCreate``
        mutation.

        :param name: Group display name.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"name": name})
    rtnval = GraphQLRequestBody(
        query=GROUP_CREATE_MUTATION, variables=variables,
        operation_name="GroupCreate")
    return rtnval


def build_groupupdate(*, group_id: str,
                      name: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``groupUpdate``
        mutation.

        :param group_id: Provider-assigned group identifier.
        :param name: New display name, or ``None`` to leave unchanged.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": group_id, "name": name})
    rtnval = GraphQLRequestBody(
        query=GROUP_UPDATE_MUTATION, variables=variables,
        operation_name="GroupUpdate")
    return rtnval


def build_groupdelete(*, group_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``groupDelete``
        mutation.

        :param group_id: Provider-assigned group identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": group_id})
    rtnval = GraphQLRequestBody(
        query=GROUP_DELETE_MUTATION, variables=variables,
        operation_name="GroupDelete")
    return rtnval


__all__ = [
    "build_groupcreate",
    "build_groupupdate",
    "build_groupdelete",
    "GROUP_CREATE_MUTATION",
    "GROUP_UPDATE_MUTATION",
    "GROUP_DELETE_MUTATION",
]
