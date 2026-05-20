"""
    .. module:: build_connector_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builders
                   for the Twingate connector lifecycle mutations
                   (``connectorCreate``, ``connectorGenerateTokens``,
                   ``connectorDelete``).

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.
    DO NOT EDIT BY HAND once GraphQL introspection codegen is live; regenerate
    via ``python -m automojo.restclient.twingate._codegen.import_schema``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

from automojo.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from automojo.restclient.twingate.queries.buildersupport import build_variables


CONNECTOR_CREATE_MUTATION = (
    "mutation ConnectorCreate($name: String, $remoteNetworkId: ID!) {"
    " connectorCreate(name: $name, remoteNetworkId: $remoteNetworkId) {"
    " ok error entity { id name state remoteNetwork { id } }"
    " } }"
)

CONNECTOR_GENERATE_TOKENS_MUTATION = (
    "mutation ConnectorGenerateTokens($connectorId: ID!) {"
    " connectorGenerateTokens(connectorId: $connectorId) {"
    " ok error connectorTokens { accessToken refreshToken }"
    " } }"
)

CONNECTOR_DELETE_MUTATION = (
    "mutation ConnectorDelete($id: ID!) {"
    " connectorDelete(id: $id) { ok error }"
    " }"
)


def build_connectorcreate(*, remote_network_id: str,
                          name: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``connectorCreate``
        mutation.

        :param remote_network_id: Parent remote-network identifier.
        :param name: Optional connector display name. ``None`` lets the
            control plane auto-assign a name.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "remoteNetworkId": remote_network_id,
        "name": name,
    })
    rtnval = GraphQLRequestBody(
        query=CONNECTOR_CREATE_MUTATION, variables=variables,
        operation_name="ConnectorCreate")
    return rtnval


def build_connectorgeneratetokens(*, connector_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``connectorGenerateTokens`` mutation.

        :param connector_id: Provider-assigned connector identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"connectorId": connector_id})
    rtnval = GraphQLRequestBody(
        query=CONNECTOR_GENERATE_TOKENS_MUTATION, variables=variables,
        operation_name="ConnectorGenerateTokens")
    return rtnval


def build_connectordelete(*, connector_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``connectorDelete``
        mutation.

        :param connector_id: Provider-assigned connector identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": connector_id})
    rtnval = GraphQLRequestBody(
        query=CONNECTOR_DELETE_MUTATION, variables=variables,
        operation_name="ConnectorDelete")
    return rtnval


__all__ = [
    "build_connectorcreate",
    "build_connectorgeneratetokens",
    "build_connectordelete",
    "CONNECTOR_CREATE_MUTATION",
    "CONNECTOR_GENERATE_TOKENS_MUTATION",
    "CONNECTOR_DELETE_MUTATION",
]
