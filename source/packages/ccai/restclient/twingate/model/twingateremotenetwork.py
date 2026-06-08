"""
    .. module:: twingateremotenetwork
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateRemoteNetwork`
                   ``SchemaObject`` DTO for a Twingate ``RemoteNetwork`` node.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.base.schemaobject import SchemaObject
from ccai.restclient.base.schemafield import Field


class TwingateRemoteNetwork(SchemaObject):
    """
        Typed projection of a Twingate ``RemoteNetwork`` GraphQL node.

        :var remote_network_id: Provider-assigned stable identifier.
        :var name: Display name of the remote network.
        :var location: Network location token (for example ``AWS``).
    """

    remote_network_id: str = Field(
        str, required=True, description="Remote network id.")
    name: str = Field(
        str, required=True, description="Remote network display name.")
    location: str = Field(
        str, required=False, default="", description="Network location token.")


__all__ = ["TwingateRemoteNetwork"]
