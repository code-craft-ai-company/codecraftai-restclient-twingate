"""
    .. module:: build_resourceaccess_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builders
                   for the Twingate resource-access assignment mutations
                   (``resourceAccessAdd``, ``resourceAccessRemove``).

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.
    DO NOT EDIT BY HAND once GraphQL introspection codegen is live; regenerate
    via ``python -m automojo.restclient.twingate._codegen.import_schema``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from automojo.restclient.twingate.queries.buildersupport import build_variables


RESOURCE_ACCESS_ADD_MUTATION = (
    "mutation ResourceAccessAdd($principalId: ID!, $resourceId: ID!) {"
    " resourceAccessAdd(principalId: $principalId,"
    " resourceId: $resourceId) { ok error }"
    " }"
)

RESOURCE_ACCESS_REMOVE_MUTATION = (
    "mutation ResourceAccessRemove($principalId: ID!, $resourceId: ID!) {"
    " resourceAccessRemove(principalId: $principalId,"
    " resourceId: $resourceId) { ok error }"
    " }"
)


def build_resourceaccessadd(*, group_id: str,
                            resource_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``resourceAccessAdd`` mutation binding a group to a resource.

        :param group_id: Provider-assigned group identifier (the
            GraphQL ``principalId``).
        :param resource_id: Provider-assigned resource identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "principalId": group_id,
        "resourceId": resource_id,
    })
    rtnval = GraphQLRequestBody(
        query=RESOURCE_ACCESS_ADD_MUTATION, variables=variables,
        operation_name="ResourceAccessAdd")
    return rtnval


def build_resourceaccessremove(*, group_id: str,
                               resource_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate
        ``resourceAccessRemove`` mutation removing a group from a resource.

        :param group_id: Provider-assigned group identifier (the
            GraphQL ``principalId``).
        :param resource_id: Provider-assigned resource identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={
        "principalId": group_id,
        "resourceId": resource_id,
    })
    rtnval = GraphQLRequestBody(
        query=RESOURCE_ACCESS_REMOVE_MUTATION, variables=variables,
        operation_name="ResourceAccessRemove")
    return rtnval


__all__ = [
    "build_resourceaccessadd",
    "build_resourceaccessremove",
    "RESOURCE_ACCESS_ADD_MUTATION",
    "RESOURCE_ACCESS_REMOVE_MUTATION",
]
