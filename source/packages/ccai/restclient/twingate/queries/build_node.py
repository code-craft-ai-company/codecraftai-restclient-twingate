"""
    .. module:: build_node
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the single-entity ``get``-by-id
                   GraphQL query builders for the Twingate top-level Query
                   fields ``resource``, ``group``, ``connector``,
                   ``remoteNetwork`` and ``device``.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.
    DO NOT EDIT BY HAND once GraphQL introspection codegen is live; regenerate
    via ``python -m ccai.restclient.twingate._codegen.import_schema``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from ccai.restclient.twingate.queries.buildersupport import build_variables


RESOURCE_QUERY = (
    "query GetResource($id: ID!) {"
    " resource(id: $id) { id name address { value } remoteNetwork { id } }"
    " }"
)

GROUP_QUERY = (
    "query GetGroup($id: ID!) {"
    " group(id: $id) { id name }"
    " }"
)

CONNECTOR_QUERY = (
    "query GetConnector($id: ID!) {"
    " connector(id: $id) { id name state remoteNetwork { id name } }"
    " }"
)

REMOTE_NETWORK_QUERY = (
    "query GetRemoteNetwork($id: ID!) {"
    " remoteNetwork(id: $id) { id name location }"
    " }"
)

DEVICE_QUERY = (
    "query GetDevice($id: ID!) {"
    " device(id: $id) { id name osName lastConnectedAt isTrusted }"
    " }"
)


def build_resource(*, resource_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``resource``
        single-entity query.

        :param resource_id: Provider-assigned resource identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": resource_id})
    rtnval = GraphQLRequestBody(
        query=RESOURCE_QUERY, variables=variables,
        operation_name="GetResource")
    return rtnval


def build_group(*, group_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``group``
        single-entity query.

        :param group_id: Provider-assigned group identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": group_id})
    rtnval = GraphQLRequestBody(
        query=GROUP_QUERY, variables=variables, operation_name="GetGroup")
    return rtnval


def build_connector(*, connector_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``connector``
        single-entity query.

        :param connector_id: Provider-assigned connector identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": connector_id})
    rtnval = GraphQLRequestBody(
        query=CONNECTOR_QUERY, variables=variables,
        operation_name="GetConnector")
    return rtnval


def build_remotenetwork(*, remote_network_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``remoteNetwork``
        single-entity query.

        :param remote_network_id: Provider-assigned remote-network id.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": remote_network_id})
    rtnval = GraphQLRequestBody(
        query=REMOTE_NETWORK_QUERY, variables=variables,
        operation_name="GetRemoteNetwork")
    return rtnval


def build_device(*, device_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``device``
        single-entity query.

        :param device_id: Provider-assigned device identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": device_id})
    rtnval = GraphQLRequestBody(
        query=DEVICE_QUERY, variables=variables, operation_name="GetDevice")
    return rtnval


__all__ = [
    "build_resource",
    "build_group",
    "build_connector",
    "build_remotenetwork",
    "build_device",
    "RESOURCE_QUERY",
    "GROUP_QUERY",
    "CONNECTOR_QUERY",
    "REMOTE_NETWORK_QUERY",
    "DEVICE_QUERY",
]
