"""
    .. module:: apigroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the Twingate api groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.apigroups.resourcesgroup import ResourcesGroup
from automojo.restclient.twingate.apigroups.groupsgroup import GroupsGroup
from automojo.restclient.twingate.apigroups.connectorsgroup import ConnectorsGroup
from automojo.restclient.twingate.apigroups.remotenetworksgroup import (
    RemoteNetworksGroup
)
from automojo.restclient.twingate.apigroups.devicesgroup import DevicesGroup


__all__ = [
    "ResourcesGroup",
    "GroupsGroup",
    "ConnectorsGroup",
    "RemoteNetworksGroup",
    "DevicesGroup",
]
