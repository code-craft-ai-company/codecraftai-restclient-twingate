"""
    .. module:: graphqlrequestbody
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`GraphQLRequestBody` frozen
                   dataclass produced by the typed query and mutation builders.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class GraphQLRequestBody:
    """
        Typed GraphQL request body produced by the generated query and
        mutation builders under ``queries/`` and ``mutations/``.

        The HTTP layer POSTs this body as the JSON document::

            {"query": ..., "variables": ..., "operationName": ...}

        :param query: The GraphQL query or mutation document text.
        :param variables: The GraphQL variables map. ``None``-valued
            entries are omitted by the builders so the variables map
            never carries unset arguments.
        :param operation_name: The GraphQL ``operationName`` selector, or
            ``None`` when the document declares a single anonymous
            operation.
    """
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)
    operation_name: Optional[str] = None

    def as_payload(self) -> Dict[str, Any]:
        """
            Render this request body as the JSON-serialisable dictionary
            the Twingate GraphQL endpoint expects.

            :returns: A dictionary with ``query``, ``variables`` and
                ``operationName`` keys.
        """
        payload: Dict[str, Any] = {
            "query": self.query,
            "variables": dict(self.variables),
        }

        if self.operation_name is not None:
            payload["operationName"] = self.operation_name

        rtnval = payload
        return rtnval


__all__ = ["GraphQLRequestBody"]
