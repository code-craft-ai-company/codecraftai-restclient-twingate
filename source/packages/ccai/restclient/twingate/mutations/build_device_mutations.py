"""
    .. module:: build_device_mutations
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the typed GraphQL mutation builder
                   for the Twingate ``deviceDelete`` mutation.

    HAND-AUTHORED — see the "Codegen Decision" section of ``AGENTS.md``.
    DO NOT EDIT BY HAND once GraphQL introspection codegen is live; regenerate
    via ``python -m ccai.restclient.twingate._codegen.import_schema``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from ccai.restclient.twingate.queries.buildersupport import build_variables


DEVICE_DELETE_MUTATION = (
    "mutation DeviceDelete($id: ID!) {"
    " deviceDelete(id: $id) { ok error }"
    " }"
)


def build_devicedelete(*, device_id: str) -> GraphQLRequestBody:
    """
        Build the GraphQL request body for the Twingate ``deviceDelete``
        mutation.

        :param device_id: Provider-assigned device identifier.

        :returns: A :class:`GraphQLRequestBody`.
    """
    variables = build_variables(candidate={"id": device_id})
    rtnval = GraphQLRequestBody(
        query=DEVICE_DELETE_MUTATION, variables=variables,
        operation_name="DeviceDelete")
    return rtnval


__all__ = ["build_devicedelete", "DEVICE_DELETE_MUTATION"]
