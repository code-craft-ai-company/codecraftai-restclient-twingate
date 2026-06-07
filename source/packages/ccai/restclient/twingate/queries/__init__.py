"""
    .. module:: queries
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the typed GraphQL query builders
                   for the Twingate top-level Query fields.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.twingate.queries.build_resources import build_resources
from ccai.restclient.twingate.queries.build_groups import build_groups
from ccai.restclient.twingate.queries.build_connectors import build_connectors
from ccai.restclient.twingate.queries.build_remotenetworks import (
    build_remotenetworks
)
from ccai.restclient.twingate.queries.build_devices import build_devices
from ccai.restclient.twingate.queries.build_node import (
    build_resource,
    build_group,
    build_connector,
    build_remotenetwork,
    build_device,
)


__all__ = [
    "build_resources",
    "build_groups",
    "build_connectors",
    "build_remotenetworks",
    "build_devices",
    "build_resource",
    "build_group",
    "build_connector",
    "build_remotenetwork",
    "build_device",
]
