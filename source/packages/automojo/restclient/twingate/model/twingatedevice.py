"""
    .. module:: twingatedevice
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateDevice`
                   ``SchemaObject`` DTO for a Twingate ``Device`` node.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.base.schemaobject import SchemaObject
from automojo.restclient.base.schemafield import Field


class TwingateDevice(SchemaObject):
    """
        Typed projection of a Twingate ``Device`` GraphQL node.

        Twingate ``Device`` nodes are the trusted-client registrations on a
        network — distinct from connectors. They do not carry an overlay
        address (Twingate does not assign per-client overlay IPs).

        :var device_id: Provider-assigned stable identifier.
        :var name: Device display name as reported by the agent.
        :var os_name: Operating-system string reported by the agent.
        :var last_connected_at: ISO-8601 last-connected timestamp.
        :var is_trusted: Whether the device is currently trusted.
    """

    device_id: str = Field(str, required=True, description="Device id.")
    name: str = Field(
        str, required=False, default="", description="Device display name.")
    os_name: str = Field(
        str, required=False, default="",
        description="Operating-system string.")
    last_connected_at: str = Field(
        str, required=False, default="",
        description="ISO-8601 last-connected timestamp.")
    is_trusted: bool = Field(
        bool, required=False, default=False,
        description="Whether the device is trusted.")


__all__ = ["TwingateDevice"]
