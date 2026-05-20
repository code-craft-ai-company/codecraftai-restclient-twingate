"""
    .. module:: mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the typed GraphQL mutation builders
                   for the Twingate top-level Mutation fields.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.mutations.build_resource_mutations import (
    build_resourcecreate,
    build_resourceupdate,
    build_resourcedelete,
)
from automojo.restclient.twingate.mutations.build_group_mutations import (
    build_groupcreate,
    build_groupupdate,
    build_groupdelete,
)
from automojo.restclient.twingate.mutations.build_connector_mutations import (
    build_connectorcreate,
    build_connectorgeneratetokens,
    build_connectordelete,
)
from automojo.restclient.twingate.mutations.build_remotenetwork_mutations import (
    build_remotenetworkcreate,
    build_remotenetworkupdate,
    build_remotenetworkdelete,
)
from automojo.restclient.twingate.mutations.build_resourceaccess_mutations import (
    build_resourceaccessadd,
    build_resourceaccessremove,
)
from automojo.restclient.twingate.mutations.build_device_mutations import (
    build_devicedelete,
)


__all__ = [
    "build_resourcecreate",
    "build_resourceupdate",
    "build_resourcedelete",
    "build_groupcreate",
    "build_groupupdate",
    "build_groupdelete",
    "build_connectorcreate",
    "build_connectorgeneratetokens",
    "build_connectordelete",
    "build_remotenetworkcreate",
    "build_remotenetworkupdate",
    "build_remotenetworkdelete",
    "build_resourceaccessadd",
    "build_resourceaccessremove",
    "build_devicedelete",
]
