"""
    .. module:: twingate
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: The ``automojo-restclient-twingate`` package — a typed,
                   aspect-driven GraphQL client for the Twingate Admin API.

    The package re-exports :class:`TwingateClient` (which implements the
    :class:`IVPNControlPlane` protocol), the :class:`AspectsTwingate`
    behaviour bundle and the :class:`GraphQLRequestBody` request dataclass.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.twingateclient import (
    TwingateClient, GRAPHQL_LEAF
)
from automojo.restclient.twingate.aspectstwingate import (
    AspectsTwingate, DEFAULT_TWINGATE_ASPECTS
)
from automojo.restclient.twingate.graphqlrequestbody import GraphQLRequestBody


__all__ = [
    "TwingateClient",
    "GRAPHQL_LEAF",
    "AspectsTwingate",
    "DEFAULT_TWINGATE_ASPECTS",
    "GraphQLRequestBody",
]
