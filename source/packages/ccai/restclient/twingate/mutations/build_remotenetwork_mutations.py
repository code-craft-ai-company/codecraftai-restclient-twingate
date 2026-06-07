"""
    .. module:: build_remotenetwork_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builders
                   for the Twingate remote-network lifecycle mutations
                   (``remoteNetworkCreate``, ``remoteNetworkUpdate``,
                   ``remoteNetworkDelete``).

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


REMOTE_NETWORK_CREATE_MUTATION = (
    "mutation RemoteNetworkCreate($location: String, $name: String!) {"
    " remoteNetworkCreate(location: $location, name: $name) {"
    " ok error entity { id name location }"
    " } }"
)

REMOTE_NETWORK_UPDATE_MUTATION = (
    "mutation RemoteNetworkUpdate($id: ID!, $location: String,"
    " $name: String) {"
    " remoteNetworkUpdate(id: $id, location: $location, name: $name) {"
    " ok error entity { id name location }"
    " } }"
)

REMOTE_NETWORK_DELETE_MUTATION = (
    "mutation RemoteNetworkDelete($id: ID!) {"
    " remoteNetworkDelete(id: $id) { ok error }"
    " }"
)


def build_remotenetworkcreate(*, name: str,
                              location: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``remoteNetworkCreate`` mutation.

        :param name: Remote-network display name.
        :param location: Optional location token (for example ``AWS``).

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"name": name, "location": location})
    rtnval = GraphQLRequestBody(
        query=REMOTE_NETWORK_CREATE_MUTATION, variables=variables,
        operation_name="RemoteNetworkCreate")
    return rtnval


def build_remotenetworkupdate(*, remote_network_id: str,
                              name: Optional[str] = None,
                              location: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``remoteNetworkUpdate`` mutation.

        :param remote_network_id: Provider-assigned remote-network id.
        :param name: New display name, or ``None`` to leave unchanged.
        :param location: New location token, or ``None`` to leave unchanged.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "id": remote_network_id,
        "name": name,
        "location": location,
    })
    rtnval = GraphQLRequestBody(
        query=REMOTE_NETWORK_UPDATE_MUTATION, variables=variables,
        operation_name="RemoteNetworkUpdate")
    return rtnval


def build_remotenetworkdelete(*, remote_network_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``remoteNetworkDelete`` mutation.

        :param remote_network_id: Provider-assigned remote-network id.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": remote_network_id})
    rtnval = GraphQLRequestBody(
        query=REMOTE_NETWORK_DELETE_MUTATION, variables=variables,
        operation_name="RemoteNetworkDelete")
    return rtnval


__all__ = [
    "build_remotenetworkcreate",
    "build_remotenetworkupdate",
    "build_remotenetworkdelete",
    "REMOTE_NETWORK_CREATE_MUTATION",
    "REMOTE_NETWORK_UPDATE_MUTATION",
    "REMOTE_NETWORK_DELETE_MUTATION",
]
