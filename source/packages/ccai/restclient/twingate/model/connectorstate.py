"""
    .. module:: connectorstate
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`ConnectorState` enum
                   mirroring the Twingate ``ConnectorState`` GraphQL enum.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``. The
    member set mirrors the documented Twingate ``ConnectorState`` enum values
    verbatim. A maintainer with a live network can run introspection to
    confirm or extend the set.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import enum


class ConnectorState(enum.Enum):
    """
        Mirror of the Twingate ``ConnectorState`` GraphQL enum. Members
        match the upstream enum values verbatim.
    """
    ALIVE = "ALIVE"
    DEAD_NO_HEARTBEAT = "DEAD_NO_HEARTBEAT"
    DEAD_NO_RELAYS = "DEAD_NO_RELAYS"
    DEAD_HEARTBEAT_TOO_OLD = "DEAD_HEARTBEAT_TOO_OLD"


__all__ = ["ConnectorState"]
