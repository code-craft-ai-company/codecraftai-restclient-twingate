"""
    .. module:: twingateresource
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateResource`
                   ``SchemaObject`` DTO for a Twingate ``Resource`` node.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``. This
    DTO would be GraphQL-introspection generated; it is hand-authored from the
    documented Twingate ``Resource`` type because live introspection requires
    a network + API token unavailable at build time.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Dict, List

from ccai.restclient.base.schemaobject import SchemaObject
from ccai.restclient.base.schemafield import Field


class TwingateResource(SchemaObject):
    """
        Typed projection of a Twingate ``Resource`` GraphQL node.

        :var resource_id: Provider-assigned stable identifier.
        :var name: Display name of the resource.
        :var address: Address shape — FQDN, IP, or CIDR.
        :var remote_network_id: Identifier of the parent ``RemoteNetwork``.
        :var protocols: Allowed protocol map keyed by protocol name.
    """

    resource_id: str = Field(str, required=True, description="Resource id.")
    name: str = Field(str, required=True, description="Resource display name.")
    address: str = Field(str, required=True, description="FQDN, IP, or CIDR.")
    remote_network_id: str = Field(
        str, required=False, default="",
        description="Parent remote-network identifier.")
    protocols: Dict[str, List[int]] = Field(
        dict, required=False, description="Allowed protocol map.")


__all__ = ["TwingateResource"]
