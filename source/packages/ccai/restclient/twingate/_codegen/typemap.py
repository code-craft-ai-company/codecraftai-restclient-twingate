"""
    .. module:: typemap
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that maps GraphQL scalar type names to Python types
                   for the schema-import emitter.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import datetime

from typing import Any, Dict


# GraphQL scalar type name -> (python type object, python type source name).
GRAPHQL_SCALAR_TYPEMAP: Dict[str, Any] = {
    "String": str,
    "Int": int,
    "Boolean": bool,
    "ID": str,
    "Float": float,
    "DateTime": datetime.datetime,
    "JSON": dict,
}


# GraphQL scalar type name -> python type expression as used in emitted code.
GRAPHQL_SCALAR_TYPENAMES: Dict[str, str] = {
    "String": "str",
    "Int": "int",
    "Boolean": "bool",
    "ID": "str",
    "Float": "float",
    "DateTime": "datetime.datetime",
    "JSON": "Dict[str, Any]",
}


def python_type_for_scalar(*, scalar_name: str) -> Any:
    """
        Resolve the Python type object for a GraphQL scalar type name.

        :param scalar_name: The GraphQL scalar type name.

        :returns: The Python type object, defaulting to :class:`str` for
            unrecognised scalar names so the emitter never fails closed.
    """
    rtnval = GRAPHQL_SCALAR_TYPEMAP.get(scalar_name, str)
    return rtnval


def python_typename_for_scalar(*, scalar_name: str) -> str:
    """
        Resolve the emitted Python type expression for a GraphQL scalar
        type name.

        :param scalar_name: The GraphQL scalar type name.

        :returns: The Python type expression string, defaulting to ``str``
            for unrecognised scalar names.
    """
    rtnval = GRAPHQL_SCALAR_TYPENAMES.get(scalar_name, "str")
    return rtnval


__all__ = [
    "GRAPHQL_SCALAR_TYPEMAP",
    "GRAPHQL_SCALAR_TYPENAMES",
    "python_type_for_scalar",
    "python_typename_for_scalar",
]
