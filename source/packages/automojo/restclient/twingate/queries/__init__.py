"""
    .. module:: queries
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the typed GraphQL query builders
                   for the Twingate top-level Query fields.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.queries.build_resources import build_resources
from automojo.restclient.twingate.queries.build_groups import build_groups
from automojo.restclient.twingate.queries.build_connectors import build_connectors
from automojo.restclient.twingate.queries.build_remotenetworks import (
    build_remotenetworks
)
from automojo.restclient.twingate.queries.build_devices import build_devices
from automojo.restclient.twingate.queries.build_node import (
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
