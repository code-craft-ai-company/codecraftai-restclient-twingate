"""
    .. module:: twingategroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateGroup`
                   ``SchemaObject`` DTO for a Twingate ``Group`` node.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import List

from ccai.restclient.base.schemaobject import SchemaObject
from ccai.restclient.base.schemafield import Field


class TwingateGroup(SchemaObject):
    """
        Typed projection of a Twingate ``Group`` GraphQL node.

        :var group_id: Provider-assigned stable identifier.
        :var name: Display name of the group.
        :var user_ids: Identifiers of users in the group.
    """

    group_id: str = Field(str, required=True, description="Group id.")
    name: str = Field(str, required=True, description="Group display name.")
    user_ids: List[str] = Field(
        list, required=False, description="Member user identifiers.")


__all__ = ["TwingateGroup"]
