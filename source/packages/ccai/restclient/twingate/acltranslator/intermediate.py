"""
    .. module:: intermediate
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the intermediate representation
                   dataclasses produced by the ACL parser and consumed by
                   the differ and executor.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class IntermediateResource:
    """
        Provider-neutral intermediate resource record.

        :param name: Resource display name — the stable join key.
        :param address: FQDN, IP, or CIDR.
        :param remote_network_id: Parent remote-network identifier.
    """
    name: str
    address: str
    remote_network_id: str


@dataclass(frozen=True)
class IntermediateGroup:
    """
        Provider-neutral intermediate group record.

        :param name: Group display name — the stable join key.
    """
    name: str


@dataclass(frozen=True)
class IntermediateEdge:
    """
        Provider-neutral intermediate resource-group assignment record.

        :param group_name: Display name of the group side of the edge.
        :param resource_name: Display name of the resource side.
    """
    group_name: str
    resource_name: str


@dataclass
class IntermediateModel:
    """
        The full parsed intermediate representation of a Tailscale-shaped
        flat-ACL document.

        :param resources: Desired resources keyed by name uniqueness.
        :param groups: Desired groups keyed by name uniqueness.
        :param edges: Desired resource-group assignments.
    """
    resources: List[IntermediateResource] = field(default_factory=list)
    groups: List[IntermediateGroup] = field(default_factory=list)
    edges: List[IntermediateEdge] = field(default_factory=list)


__all__ = [
    "IntermediateResource",
    "IntermediateGroup",
    "IntermediateEdge",
    "IntermediateModel",
]
