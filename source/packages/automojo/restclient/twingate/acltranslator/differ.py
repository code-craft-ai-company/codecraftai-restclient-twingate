"""
    .. module:: differ
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :func:`build_apply_plan` function
                   which set-diffs an intermediate model against the current
                   Twingate state to produce a three-phase :class:`ApplyPlan`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, List

from automojo.restclient.twingate.acltranslator.intermediate import (
    IntermediateResource, IntermediateGroup, IntermediateEdge,
    IntermediateModel
)
from automojo.restclient.twingate.acltranslator.plan import ApplyPlan
from automojo.restclient.twingate.model.twingateresource import TwingateResource
from automojo.restclient.twingate.model.twingategroup import TwingateGroup


def build_apply_plan(*, desired: IntermediateModel,
                     current_resources: List[TwingateResource],
                     current_groups: List[TwingateGroup],
                     current_edges: List[IntermediateEdge]) -> ApplyPlan:
    """
        Set-diff a desired intermediate model against the current Twingate
        state and build a three-phase :class:`ApplyPlan`.

        The diff is order-independent — it works against name-keyed sets —
        so two ``acl_doc`` documents that differ only in element ordering
        produce the same plan. When ``desired`` already matches the current
        state every phase is empty, which is what makes a second
        ``apply_acl`` issue zero mutations.

        :param desired: The parsed desired intermediate model.
        :param current_resources: Resources currently on the network.
        :param current_groups: Groups currently on the network.
        :param current_edges: Resource-group assignments currently on the
            network, expressed as :class:`IntermediateEdge` records.

        :returns: A three-phase :class:`ApplyPlan`.
    """
    plan = ApplyPlan()

    _diff_resources(
        plan=plan, desired=desired.resources,
        current_resources=current_resources)
    _diff_groups(
        plan=plan, desired=desired.groups, current_groups=current_groups)
    _diff_edges(
        plan=plan, desired=desired.edges, current_edges=current_edges)

    rtnval = plan
    return rtnval


def _diff_resources(*, plan: ApplyPlan,
                    desired: List[IntermediateResource],
                    current_resources: List[TwingateResource]) -> None:
    """
        Populate the resource phase of ``plan`` by name-keyed set diff.

        :param plan: The plan being built.
        :param desired: Desired intermediate resources.
        :param current_resources: Resources currently on the network.

        :returns: ``None``.
    """
    current_by_name: Dict[str, TwingateResource] = {}
    for resource in current_resources:
        current_by_name[resource.name] = resource

    desired_names = set()
    for resource in desired:
        desired_names.add(resource.name)
        if resource.name not in current_by_name:
            plan.resources_create.append(resource)
        else:
            existing = current_by_name[resource.name]
            if existing.address != resource.address:
                plan.resources_update.append(resource)

    delete_names = []
    for resource in current_resources:
        if resource.name not in desired_names:
            delete_names.append(resource.name)

    plan.resources_delete.extend(sorted(delete_names))
    return None


def _diff_groups(*, plan: ApplyPlan, desired: List[IntermediateGroup],
                 current_groups: List[TwingateGroup]) -> None:
    """
        Populate the group phase of ``plan`` by name-keyed set diff.

        :param plan: The plan being built.
        :param desired: Desired intermediate groups.
        :param current_groups: Groups currently on the network.

        :returns: ``None``.
    """
    current_names = set()
    for group in current_groups:
        current_names.add(group.name)

    desired_names = set()
    for group in desired:
        desired_names.add(group.name)
        if group.name not in current_names:
            plan.groups_create.append(group)

    delete_names = []
    for group in current_groups:
        if group.name not in desired_names:
            delete_names.append(group.name)

    plan.groups_delete.extend(sorted(delete_names))
    return None


def _diff_edges(*, plan: ApplyPlan, desired: List[IntermediateEdge],
                current_edges: List[IntermediateEdge]) -> None:
    """
        Populate the assignment phase of ``plan`` by set diff.

        :param plan: The plan being built.
        :param desired: Desired intermediate edges.
        :param current_edges: Assignments currently on the network.

        :returns: ``None``.
    """
    desired_set = set(desired)
    current_set = set(current_edges)

    add_edges = sorted(
        desired_set - current_set,
        key=lambda e: (e.group_name, e.resource_name))
    remove_edges = sorted(
        current_set - desired_set,
        key=lambda e: (e.group_name, e.resource_name))

    plan.edges_add.extend(add_edges)
    plan.edges_remove.extend(remove_edges)
    return None


__all__ = ["build_apply_plan"]
