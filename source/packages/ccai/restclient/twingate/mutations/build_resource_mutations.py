"""
    .. module:: build_resource_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builders
                   for the Twingate resource lifecycle mutations
                   (``resourceCreate``, ``resourceUpdate``,
                   ``resourceDelete``).

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


RESOURCE_CREATE_MUTATION = (
    "mutation ResourceCreate($address: String!, $name: String!,"
    " $remoteNetworkId: ID!) {"
    " resourceCreate(address: $address, name: $name,"
    " remoteNetworkId: $remoteNetworkId) {"
    " ok error entity { id name address { value } remoteNetwork { id } }"
    " } }"
)

RESOURCE_UPDATE_MUTATION = (
    "mutation ResourceUpdate($address: String, $id: ID!, $name: String) {"
    " resourceUpdate(address: $address, id: $id, name: $name) {"
    " ok error entity { id name address { value } remoteNetwork { id } }"
    " } }"
)

RESOURCE_DELETE_MUTATION = (
    "mutation ResourceDelete($id: ID!) {"
    " resourceDelete(id: $id) { ok error }"
    " }"
)


def build_resourcecreate(*, name: str, address: str,
                         remote_network_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``resourceCreate``
        mutation.

        :param name: Resource display name.
        :param address: FQDN, IP, or CIDR.
        :param remote_network_id: Parent remote-network identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "name": name,
        "address": address,
        "remoteNetworkId": remote_network_id,
    })
    rtnval = GraphQLRequestBody(
        query=RESOURCE_CREATE_MUTATION, variables=variables,
        operation_name="ResourceCreate")
    return rtnval


def build_resourceupdate(*, resource_id: str, name: Optional[str] = None,
                         address: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``resourceUpdate``
        mutation.

        :param resource_id: Provider-assigned resource identifier.
        :param name: New display name, or ``None`` to leave unchanged.
        :param address: New address, or ``None`` to leave unchanged.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "id": resource_id,
        "name": name,
        "address": address,
    })
    rtnval = GraphQLRequestBody(
        query=RESOURCE_UPDATE_MUTATION, variables=variables,
        operation_name="ResourceUpdate")
    return rtnval


def build_resourcedelete(*, resource_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``resourceDelete``
        mutation.

        :param resource_id: Provider-assigned resource identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": resource_id})
    rtnval = GraphQLRequestBody(
        query=RESOURCE_DELETE_MUTATION, variables=variables,
        operation_name="ResourceDelete")
    return rtnval


__all__ = [
    "build_resourcecreate",
    "build_resourceupdate",
    "build_resourcedelete",
    "RESOURCE_CREATE_MUTATION",
    "RESOURCE_UPDATE_MUTATION",
    "RESOURCE_DELETE_MUTATION",
]
