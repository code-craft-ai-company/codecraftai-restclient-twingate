"""
    .. module:: parser
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :func:`parse_acl_document`
                   function which translates a Tailscale-shaped flat-ACL
                   JSON document into the provider-neutral intermediate
                   representation.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Dict, List

from automojo.errors.exceptions import SemanticError

from automojo.restclient.twingate.acltranslator.intermediate import (
    IntermediateResource, IntermediateGroup, IntermediateEdge,
    IntermediateModel
)


def parse_acl_document(*, acl_doc: Dict[str, Any],
                       default_remote_network_id: str) -> IntermediateModel:
    """
        Parse a Tailscale-shaped flat-ACL JSON document into the
        provider-neutral intermediate representation.

        The Tailscale-shaped document is expected to expose:

        - ``hosts`` — a name to address mapping. Each entry becomes an
          :class:`IntermediateResource`.
        - ``groups`` — a group-name to member-list mapping. Each key
          becomes an :class:`IntermediateGroup`.
        - ``acls`` — a list of ``{"action", "src", "dst"}`` rules. Each
          ``src`` group paired with each ``dst`` host becomes an
          :class:`IntermediateEdge`.

        The translation is honest, not faithful: Twingate has no flat-ACL
        primitive. ``src`` entries that are not declared groups and ``dst``
        entries that are not declared hosts are rejected so the translation
        never silently drops a rule.

        :param acl_doc: The Tailscale-shaped flat-ACL document.
        :param default_remote_network_id: Remote-network identifier
            assigned to every resource derived from a ``hosts`` entry.

        :returns: An :class:`IntermediateModel`.

        :raises: :class:`SemanticError` when the document is structurally
            malformed.
    """
    if acl_doc is None:
        err_msg_lines = [
            "Twingate apply_acl requires a non-None 'acl_doc'.",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    if not isinstance(acl_doc, dict):
        err_msg_lines = [
            "Twingate apply_acl requires 'acl_doc' to be a dictionary.",
            f"FOUND TYPE: {type(acl_doc).__name__}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    resources = _parse_hosts(
        acl_doc=acl_doc,
        default_remote_network_id=default_remote_network_id)
    groups = _parse_groups(acl_doc=acl_doc)

    resource_names = set()
    for resource in resources:
        resource_names.add(resource.name)

    group_names = set()
    for group in groups:
        group_names.add(group.name)

    edges = _parse_acls(
        acl_doc=acl_doc,
        resource_names=resource_names,
        group_names=group_names)

    model = IntermediateModel(
        resources=resources, groups=groups, edges=edges)

    rtnval = model
    return rtnval


def _parse_hosts(*, acl_doc: Dict[str, Any],
                 default_remote_network_id: str) -> List[IntermediateResource]:
    """
        Parse the ``hosts`` block into intermediate resources.

        :param acl_doc: The Tailscale-shaped flat-ACL document.
        :param default_remote_network_id: Remote-network identifier for
            every derived resource.

        :returns: A name-sorted list of :class:`IntermediateResource`.

        :raises: :class:`SemanticError` when ``hosts`` is malformed.
    """
    hosts = acl_doc.get("hosts", {})
    if hosts is None:
        hosts = {}

    if not isinstance(hosts, dict):
        err_msg_lines = [
            "Twingate apply_acl requires 'hosts' to be a mapping.",
            f"FOUND TYPE: {type(hosts).__name__}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    resources: List[IntermediateResource] = []
    for host_name in sorted(hosts.keys()):
        address = hosts[host_name]
        if not isinstance(host_name, str) or len(host_name) == 0:
            err_msg_lines = [
                "Twingate apply_acl 'hosts' keys must be non-empty strings.",
                f"FOUND KEY: {host_name!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)
        if not isinstance(address, str) or len(address) == 0:
            err_msg_lines = [
                "Twingate apply_acl 'hosts' values must be non-empty "
                "address strings.",
                f"HOST: {host_name}",
                f"FOUND VALUE: {address!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        resource = IntermediateResource(
            name=host_name,
            address=address,
            remote_network_id=default_remote_network_id)
        resources.append(resource)

    rtnval = resources
    return rtnval


def _parse_groups(*, acl_doc: Dict[str, Any]) -> List[IntermediateGroup]:
    """
        Parse the ``groups`` block into intermediate groups.

        :param acl_doc: The Tailscale-shaped flat-ACL document.

        :returns: A name-sorted list of :class:`IntermediateGroup`.

        :raises: :class:`SemanticError` when ``groups`` is malformed.
    """
    groups_block = acl_doc.get("groups", {})
    if groups_block is None:
        groups_block = {}

    if not isinstance(groups_block, dict):
        err_msg_lines = [
            "Twingate apply_acl requires 'groups' to be a mapping.",
            f"FOUND TYPE: {type(groups_block).__name__}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    groups: List[IntermediateGroup] = []
    for group_name in sorted(groups_block.keys()):
        if not isinstance(group_name, str) or len(group_name) == 0:
            err_msg_lines = [
                "Twingate apply_acl 'groups' keys must be non-empty strings.",
                f"FOUND KEY: {group_name!r}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)
        groups.append(IntermediateGroup(name=group_name))

    rtnval = groups
    return rtnval


def _parse_acls(*, acl_doc: Dict[str, Any], resource_names: set,
                group_names: set) -> List[IntermediateEdge]:
    """
        Parse the ``acls`` rule list into intermediate edges.

        :param acl_doc: The Tailscale-shaped flat-ACL document.
        :param resource_names: The set of declared resource (host) names.
        :param group_names: The set of declared group names.

        :returns: A sorted, de-duplicated list of :class:`IntermediateEdge`.

        :raises: :class:`SemanticError` when ``acls`` is malformed or a
            rule references an undeclared group or host.
    """
    acls = acl_doc.get("acls", [])
    if acls is None:
        acls = []

    if not isinstance(acls, list):
        err_msg_lines = [
            "Twingate apply_acl requires 'acls' to be a list.",
            f"FOUND TYPE: {type(acls).__name__}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    edge_set = set()
    for rule_index in range(len(acls)):
        rule = acls[rule_index]
        if not isinstance(rule, dict):
            err_msg_lines = [
                "Twingate apply_acl 'acls' entries must be objects.",
                f"RULE INDEX: {rule_index}",
                f"FOUND TYPE: {type(rule).__name__}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        src_list = rule.get("src", [])
        dst_list = rule.get("dst", [])
        if not isinstance(src_list, list) or not isinstance(dst_list, list):
            err_msg_lines = [
                "Twingate apply_acl 'acls' rule 'src' and 'dst' must be "
                "lists.",
                f"RULE INDEX: {rule_index}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        for src_entry in src_list:
            group_name = _strip_dst_port(value=src_entry)
            if group_name not in group_names:
                err_msg_lines = [
                    "Twingate apply_acl rule 'src' references an undeclared "
                    "group.",
                    f"RULE INDEX: {rule_index}",
                    f"SRC: {src_entry}",
                    f"DECLARED GROUPS: {sorted(group_names)}",
                ]
                err_msg = os.linesep.join(err_msg_lines)
                raise SemanticError(err_msg)

            for dst_entry in dst_list:
                resource_name = _strip_dst_port(value=dst_entry)
                if resource_name not in resource_names:
                    err_msg_lines = [
                        "Twingate apply_acl rule 'dst' references an "
                        "undeclared host.",
                        f"RULE INDEX: {rule_index}",
                        f"DST: {dst_entry}",
                        f"DECLARED HOSTS: {sorted(resource_names)}",
                    ]
                    err_msg = os.linesep.join(err_msg_lines)
                    raise SemanticError(err_msg)

                edge = IntermediateEdge(
                    group_name=group_name, resource_name=resource_name)
                edge_set.add(edge)

    edges = sorted(
        edge_set, key=lambda e: (e.group_name, e.resource_name))
    rtnval = edges
    return rtnval


def _strip_dst_port(*, value: Any) -> str:
    """
        Strip a trailing ``:port`` selector from a Tailscale ``dst`` /
        ``src`` token, returning the bare name.

        :param value: The raw rule token.

        :returns: The token with any trailing ``:port`` removed.

        :raises: :class:`SemanticError` when ``value`` is not a string.
    """
    if not isinstance(value, str) or len(value) == 0:
        err_msg_lines = [
            "Twingate apply_acl rule 'src'/'dst' tokens must be non-empty "
            "strings.",
            f"FOUND VALUE: {value!r}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    colon_index = value.rfind(":")
    if colon_index > 0:
        rtnval = value[:colon_index]
    else:
        rtnval = value

    return rtnval


__all__ = ["parse_acl_document"]
