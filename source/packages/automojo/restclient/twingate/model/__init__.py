"""
    .. module:: model
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the Twingate ``SchemaObject`` DTOs
                   and enum types.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.model.twingateresource import TwingateResource
from automojo.restclient.twingate.model.twingategroup import TwingateGroup
from automojo.restclient.twingate.model.twingateconnector import TwingateConnector
from automojo.restclient.twingate.model.twingateremotenetwork import (
    TwingateRemoteNetwork
)
from automojo.restclient.twingate.model.twingatedevice import TwingateDevice
from automojo.restclient.twingate.model.connectorstate import ConnectorState


__all__ = [
    "TwingateResource",
    "TwingateGroup",
    "TwingateConnector",
    "TwingateRemoteNetwork",
    "TwingateDevice",
    "ConnectorState",
]
