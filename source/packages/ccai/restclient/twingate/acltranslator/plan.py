"""
    .. module:: plan
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the three-phase :class:`ApplyPlan`
                   produced by the differ and consumed by the executor.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass, field
from typing import List

from ccai.restclient.twingate.acltranslator.intermediate import (
    IntermediateResource, IntermediateGroup, IntermediateEdge
)


@dataclass
class ApplyPlan:
    """
        The three-phase idempotent apply plan.

        Phase 1 — resources: ``resources_create`` / ``resources_update`` /
        ``resources_delete``. Phase 2 — groups: ``groups_create`` /
        ``groups_delete``. Phase 3 — assignments: ``edges_add`` /
        ``edges_remove``.

        :param resources_create: Resources absent on the network.
        :param resources_update: Resources present but with a differing
            address.
        :param resources_delete: Resources present but no longer desired.
        :param groups_create: Groups absent on the network.
        :param groups_delete: Groups present but no longer desired.
        :param edges_add: Assignments to add.
        :param edges_remove: Assignments to remove.
    """
    resources_create: List[IntermediateResource] = field(default_factory=list)
    resources_update: List[IntermediateResource] = field(default_factory=list)
    resources_delete: List[str] = field(default_factory=list)
    groups_create: List[IntermediateGroup] = field(default_factory=list)
    groups_delete: List[str] = field(default_factory=list)
    edges_add: List[IntermediateEdge] = field(default_factory=list)
    edges_remove: List[IntermediateEdge] = field(default_factory=list)

    def mutation_count(self) -> int:
        """
            Count the total number of mutations this plan will issue.

            :returns: The sum of every create, update, delete, add and
                remove entry across all three phases. Zero indicates the
                network is already converged.
        """
        total = (
            len(self.resources_create)
            + len(self.resources_update)
            + len(self.resources_delete)
            + len(self.groups_create)
            + len(self.groups_delete)
            + len(self.edges_add)
            + len(self.edges_remove)
        )
        rtnval = total
        return rtnval

    def is_empty(self) -> bool:
        """
            Report whether the plan issues no mutations at all.

            :returns: ``True`` when :meth:`mutation_count` is zero.
        """
        rtnval = self.mutation_count() == 0
        return rtnval


__all__ = ["ApplyPlan"]
