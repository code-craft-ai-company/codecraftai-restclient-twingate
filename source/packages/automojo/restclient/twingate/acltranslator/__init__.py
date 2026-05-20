"""
    .. module:: acltranslator
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the three-phase ACL translator —
                   parser, differ and executor — used by
                   :meth:`TwingateClient.apply_acl`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.acltranslator.intermediate import (
    IntermediateResource, IntermediateGroup, IntermediateEdge,
    IntermediateModel
)
from automojo.restclient.twingate.acltranslator.plan import ApplyPlan
from automojo.restclient.twingate.acltranslator.parser import parse_acl_document
from automojo.restclient.twingate.acltranslator.differ import build_apply_plan
from automojo.restclient.twingate.acltranslator.executor import (
    execute_apply_plan
)


__all__ = [
    "IntermediateResource",
    "IntermediateGroup",
    "IntermediateEdge",
    "IntermediateModel",
    "ApplyPlan",
    "parse_acl_document",
    "build_apply_plan",
    "execute_apply_plan",
]
