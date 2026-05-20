"""
    .. module:: buildersupport
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains shared helpers used by the typed
                   query and mutation builders to produce deterministic
                   :class:`GraphQLRequestBody` instances.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``. A
    generated codegen pass would emit this helper inline into every builder;
    it is factored out by hand so the determinism rule lives in one place.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict


def build_variables(*, candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
        Build the GraphQL ``variables`` map from a candidate dictionary.

        Entries whose value is ``None`` are omitted so the variables map
        never carries unset arguments. The result is key-sorted so that
        identical inputs always produce a byte-identical serialisation.

        :param candidate: The proposed variable name to value mapping.

        :returns: A new key-sorted dictionary with ``None`` values removed.
    """
    variables: Dict[str, Any] = {}

    sorted_keys = sorted(candidate.keys())
    for key in sorted_keys:
        value = candidate[key]
        if value is None:
            continue
        variables[key] = value

    rtnval = variables
    return rtnval


__all__ = ["build_variables"]
