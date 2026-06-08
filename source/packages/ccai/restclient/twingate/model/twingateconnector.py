"""
    .. module:: twingateconnector
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateConnector`
                   ``SchemaObject`` DTO for a Twingate ``Connector`` node.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.base.schemaobject import SchemaObject
from ccai.restclient.base.schemafield import Field


class TwingateConnector(SchemaObject):
    """
        Typed projection of a Twingate ``Connector`` GraphQL node.

        :var connector_id: Provider-assigned stable identifier.
        :var name: Display name of the connector.
        :var remote_network_id: Identifier of the parent ``RemoteNetwork``.
        :var state: Connector state token (for example ``ALIVE``).
    """

    connector_id: str = Field(str, required=True, description="Connector id.")
    name: str = Field(str, required=True, description="Connector name.")
    remote_network_id: str = Field(
        str, required=False, default="",
        description="Parent remote-network identifier.")
    state: str = Field(
        str, required=False, default="", description="Connector state token.")


__all__ = ["TwingateConnector"]
