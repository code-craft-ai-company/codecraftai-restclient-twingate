"""
    .. module:: build_connectors
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :func:`build_connectors` typed
                   GraphQL query builder for the Twingate ``connectors``
                   top-level Query field.

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


CONNECTORS_QUERY = (
    "query ListConnectors($after: String) {"
    " connectors(after: $after) {"
    " pageInfo { endCursor hasNextPage }"
    " edges { node { id name state remoteNetwork { id name } } }"
    " } }"
)


def build_connectors(*, after: Optional[str] = None) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``connectors``
        query.

        :param after: Optional cursor token for the next page. ``None``
            requests the first page.

        :returns: A :class:`GraphQLRequestBody` with deterministic
            ``query``, ``variables`` and ``operationName``.
    """
    variables = build_variables(candidate={"after": after})

    rtnval = GraphQLRequestBody(
        query=CONNECTORS_QUERY,
        variables=variables,
        operation_name="ListConnectors",
    )
    return rtnval


__all__ = ["build_connectors", "CONNECTORS_QUERY"]
