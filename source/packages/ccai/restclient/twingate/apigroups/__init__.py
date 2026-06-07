"""
    .. module:: apigroups
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the Twingate api groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.twingate.apigroups.resourcesgroup import ResourcesGroup
from ccai.restclient.twingate.apigroups.groupsgroup import GroupsGroup
from ccai.restclient.twingate.apigroups.connectorsgroup import ConnectorsGroup
from ccai.restclient.twingate.apigroups.remotenetworksgroup import (
    RemoteNetworksGroup
)
from ccai.restclient.twingate.apigroups.devicesgroup import DevicesGroup


__all__ = [
    "ResourcesGroup",
    "GroupsGroup",
    "ConnectorsGroup",
    "RemoteNetworksGroup",
    "DevicesGroup",
]
