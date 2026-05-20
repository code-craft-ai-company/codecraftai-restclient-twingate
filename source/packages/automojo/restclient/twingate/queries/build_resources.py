"""
    .. module:: build_resources
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :func:`build_resources` typed
                   GraphQL query builder for the Twingate ``resources``
                   top-level Query field.

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


RESOURCES_QUERY = (
    "query ListResources($after: String) {"
    " resources(after: $after) {"
    " pageInfo { endCursor hasNextPage }"
    " edges { node { id name address { value } remoteNetwork { id }"
    " groups { edges { node { id name } } } } }"
    " } }"
)


def build_resources(*, after: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``resources``
        query.

        :param after: Optional cursor token for the next page. ``None``
            requests the first page.

        :returns: A :class:`GraphQLRequestBody` with deterministic
            ``query``, ``variables`` and ``operationName``.
    """
    variables = build_variables(candidate={"after": after})

    rtnval = GraphQLRequestBody(
        query=RESOURCES_QUERY,
        variables=variables,
        operation_name="ListResources",
    )
    return rtnval


__all__ = ["build_resources", "RESOURCES_QUERY"]
