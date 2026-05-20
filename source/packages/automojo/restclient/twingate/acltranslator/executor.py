"""
    .. module:: executor
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :func:`execute_apply_plan`
                   function which issues the mutations of a three-phase
                   :class:`ApplyPlan` against the Twingate api groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os
import time

from typing import Any, Dict

from automojo.restclient.twingate.acltranslator.plan import ApplyPlan
from automojo.restclient.twingate.aspectstwingate import AspectsTwingate
from automojo.restclient.twingate.exceptions import VPNControlPlaneACLError


def execute_apply_plan(*, plan: ApplyPlan, resources: Any,
                       groups: Any, access: Any,
                       resources_by_name: Dict[str, Any],
                       groups_by_name: Dict[str, Any],
                       aspects: AspectsTwingate) -> None:
    """
        Execute the three phases of an :class:`ApplyPlan` in order, pausing
        ``mutation_dependency_pause_seconds`` between dependent phases.

        Phase 1 mutates resources; phase 2 mutates groups; phase 3 mutates
        resource-group assignments. The name-keyed lookup dictionaries are
        updated in place as entities are created so phase 3 can resolve
        names to provider identifiers.

        :param plan: The three-phase plan to execute.
        :param resources: The resources api group.
        :param groups: The groups api group.
        :param access: The api group exposing resource-access mutations
            (the :class:`TwingateClient` passes itself or a delegate that
            exposes ``resource_access_add`` and ``resource_access_remove``).
        :param resources_by_name: Mutable map of resource name to record;
            seeded with the current network state and updated in place.
        :param groups_by_name: Mutable map of group name to record; seeded
            with the current network state and updated in place.
        :param aspects: Behaviour control for the call, including
            ``mutation_dependency_pause_seconds``.

        :returns: ``None``.

        :raises: :class:`VPNControlPlaneACLError` when an assignment
            references a name that does not resolve.
    """
    pause = aspects.mutation_dependency_pause_seconds

    # PHASE 1 — Resources.
    for resource in plan.resources_create:
        created = resources.create(
            name=resource.name,
            address=resource.address,
            remote_network_id=resource.remote_network_id,
            aspects=aspects)
        resources_by_name[resource.name] = created

    for resource in plan.resources_update:
        existing = resources_by_name.get(resource.name)
        if existing is None:
            err_msg_lines = [
                "Twingate apply_acl update phase could not resolve a "
                "resource id.",
                f"RESOURCE: {resource.name}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneACLError(err_msg)
        updated = resources.update(
            resource_id=existing.resource_id,
            name=resource.name,
            address=resource.address,
            aspects=aspects)
        resources_by_name[resource.name] = updated

    for resource_name in plan.resources_delete:
        existing = resources_by_name.get(resource_name)
        if existing is not None:
            resources.delete(
                resource_id=existing.resource_id, aspects=aspects)
            del resources_by_name[resource_name]

    if pause > 0:
        time.sleep(pause)

    # PHASE 2 — Groups.
    for group in plan.groups_create:
        created_group = groups.create(name=group.name, aspects=aspects)
        groups_by_name[group.name] = created_group

    for group_name in plan.groups_delete:
        existing_group = groups_by_name.get(group_name)
        if existing_group is not None:
            groups.delete(
                group_id=existing_group.group_id, aspects=aspects)
            del groups_by_name[group_name]

    if pause > 0:
        time.sleep(pause)

    # PHASE 3 — Resource-group assignments.
    for edge in plan.edges_add:
        group_record = groups_by_name.get(edge.group_name)
        resource_record = resources_by_name.get(edge.resource_name)
        _require_edge_endpoints(
            edge=edge, group_record=group_record,
            resource_record=resource_record)
        access.resource_access_add(
            group_id=group_record.group_id,
            resource_id=resource_record.resource_id,
            aspects=aspects)

    for edge in plan.edges_remove:
        group_record = groups_by_name.get(edge.group_name)
        resource_record = resources_by_name.get(edge.resource_name)
        if group_record is None or resource_record is None:
            # The endpoint was deleted earlier in this same apply; the
            # assignment is implicitly gone. Nothing to remove.
            continue
        access.resource_access_remove(
            group_id=group_record.group_id,
            resource_id=resource_record.resource_id,
            aspects=aspects)

    return None


def _require_edge_endpoints(*, edge, group_record, resource_record) -> None:
    """
        Verify both endpoints of an assignment edge resolved to records.

        :param edge: The :class:`IntermediateEdge` being applied.
        :param group_record: The resolved group record, or ``None``.
        :param resource_record: The resolved resource record, or ``None``.

        :returns: ``None``.

        :raises: :class:`VPNControlPlaneACLError` when either endpoint is
            unresolved.
    """
    if group_record is None:
        err_msg_lines = [
            "Twingate apply_acl assignment references an unknown group.",
            f"GROUP: {edge.group_name}",
            f"RESOURCE: {edge.resource_name}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneACLError(err_msg)

    if resource_record is None:
        err_msg_lines = [
            "Twingate apply_acl assignment references an unknown resource.",
            f"GROUP: {edge.group_name}",
            f"RESOURCE: {edge.resource_name}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneACLError(err_msg)

    return None


__all__ = ["execute_apply_plan"]
