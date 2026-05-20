"""
    .. module:: resourceprotocolsinput
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ResourceProtocolsInput`
                   ``SchemaObject`` mirroring the Twingate
                   ``ProtocolsInput`` INPUT_OBJECT type.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, List

from automojo.restclient.base.schemaobject import SchemaObject
from automojo.restclient.base.schemafield import Field


class ResourceProtocolsInput(SchemaObject):
    """
        Mirror of the Twingate ``ProtocolsInput`` GraphQL INPUT_OBJECT.

        :var allow_icmp: Whether ICMP traffic is permitted.
        :var tcp: TCP port specification dictionary.
        :var udp: UDP port specification dictionary.
    """

    allow_icmp: bool = Field(
        bool, required=False, default=True,
        description="Whether ICMP traffic is permitted.")
    tcp: Dict[str, List[int]] = Field(
        dict, required=False, description="TCP port specification.")
    udp: Dict[str, List[int]] = Field(
        dict, required=False, description="UDP port specification.")


__all__ = ["ResourceProtocolsInput"]
