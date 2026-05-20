"""
    .. module:: inputs
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that re-exports the Twingate INPUT_OBJECT
                   ``SchemaObject`` types.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.restclient.twingate.inputs.resourceprotocolsinput import (
    ResourceProtocolsInput
)


__all__ = ["ResourceProtocolsInput"]
