"""
    A stateful in-memory fake Twingate GraphQL server for apply_acl tests.

    It interprets the GraphQL ``operationName`` of each request, maintains
    resources / groups / assignments state, and answers queries and
    mutations against that state. This lets a test apply the same ACL
    document twice and observe that the second apply issues zero mutations.
"""

import json

from typing import Any, Dict, List


class FakeGraphQLResponse:
    """
        Minimal :class:`requests.Response` stand-in.
    """

    def __init__(self, *, payload: Any):
        """
            Initialize the fake response.

            :param payload: The JSON-serialisable body.

            :returns: ``None``.
        """
        self.status_code = 200
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload)
        self.headers = {}
        return

    def json(self) -> Any:
        """
            Return the decoded JSON body.

            :returns: The payload.
        """
        return self._payload


class FakeGraphQLServer:
    """
        Stateful fake Twingate GraphQL endpoint. Plug it in as a
        :class:`TwingateClient` session.
    """

    def __init__(self) -> None:
        """
            Initialize the server with empty state.

            :returns: ``None``.
        """
        self.verify = True
        self.headers: Dict[str, str] = {}
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._groups: Dict[str, Dict[str, Any]] = {}
        self._assignments: set = set()
        self._next_id = 1
        self.mutation_operations: List[str] = []
        self.all_operations: List[str] = []
        return

    def seed_resource(self, *, name: str, address: str,
                      remote_network_id: str) -> str:
        """
            Seed an existing resource into server state.

            :param name: Resource name.
            :param address: Resource address.
            :param remote_network_id: Parent remote-network id.

            :returns: The assigned resource id.
        """
        resource_id = self._mint_id(prefix="R")
        self._resources[resource_id] = {
            "id": resource_id, "name": name, "address": address,
            "remoteNetworkId": remote_network_id}
        return resource_id

    def seed_group(self, *, name: str) -> str:
        """
            Seed an existing group into server state.

            :param name: Group name.

            :returns: The assigned group id.
        """
        group_id = self._mint_id(prefix="G")
        self._groups[group_id] = {"id": group_id, "name": name}
        return group_id

    def seed_assignment(self, *, group_id: str, resource_id: str) -> None:
        """
            Seed an existing resource-group assignment.

            :param group_id: Group id.
            :param resource_id: Resource id.

            :returns: ``None``.
        """
        self._assignments.add((group_id, resource_id))
        return None

    def _mint_id(self, *, prefix: str) -> str:
        """
            Mint a fresh identifier.

            :param prefix: The id prefix.

            :returns: A unique id string.
        """
        value = f"{prefix}{self._next_id}"
        self._next_id = self._next_id + 1
        return value

    # -- session protocol ------------------------------------------------

    def prepare_request(self, request: Any) -> Any:
        """
            Echo the request back.

            :param request: The request.

            :returns: The same request.
        """
        return request

    def send(self, prepared_request: Any, **kwargs: Any) -> FakeGraphQLResponse:
        """
            Interpret a GraphQL request against server state.

            :param prepared_request: The prepared request.
            :param kwargs: Ignored transport keyword arguments.

            :returns: A :class:`FakeGraphQLResponse`.
        """
        # The client sends the body as `json=`, so it arrives on `.json`.
        # Reading `.data` returned requests' empty-list default, which is why
        # `decoded.get(...)` raised AttributeError on a list.  Bytes are still
        # decoded, so a caller that pre-encodes is handled rather than
        # silently mis-read.
        body = getattr(prepared_request, "json", None)
        if body is None:
            body = getattr(prepared_request, "data", None)
        if isinstance(body, (bytes, bytearray)):
            decoded = json.loads(body.decode("utf-8"))
        elif isinstance(body, str):
            decoded = json.loads(body)
        else:
            decoded = body

        operation = decoded.get("operationName", "")
        variables = decoded.get("variables", {})

        self.all_operations.append(operation)

        payload = self._dispatch(operation=operation, variables=variables)
        rtnval = FakeGraphQLResponse(payload=payload)
        return rtnval

    def _dispatch(self, *, operation: str,
                  variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Route an operation to its handler.

            :param operation: The GraphQL operation name.
            :param variables: The GraphQL variables.

            :returns: The response payload.
        """
        if operation == "ListResources":
            rtnval = self._handle_list_resources()
        elif operation == "ListGroups":
            rtnval = self._handle_list_groups()
        elif operation == "ResourceCreate":
            rtnval = self._handle_resource_create(variables=variables)
        elif operation == "ResourceUpdate":
            rtnval = self._handle_resource_update(variables=variables)
        elif operation == "ResourceDelete":
            rtnval = self._handle_resource_delete(variables=variables)
        elif operation == "GroupCreate":
            rtnval = self._handle_group_create(variables=variables)
        elif operation == "GroupDelete":
            rtnval = self._handle_group_delete(variables=variables)
        elif operation == "ResourceAccessAdd":
            rtnval = self._handle_access_add(variables=variables)
        elif operation == "ResourceAccessRemove":
            rtnval = self._handle_access_remove(variables=variables)
        else:
            rtnval = {"data": {}}
        return rtnval

    def _handle_list_resources(self) -> Dict[str, Any]:
        """
            Build the ``resources`` query response with nested groups.

            :returns: The response payload.
        """
        edges = []
        for resource_id in sorted(self._resources.keys()):
            resource = self._resources[resource_id]
            group_edges = []
            for group_id, res_id in sorted(self._assignments):
                if res_id == resource_id and group_id in self._groups:
                    group_edges.append({"node": {
                        "id": group_id,
                        "name": self._groups[group_id]["name"]}})
            edges.append({"node": {
                "id": resource["id"],
                "name": resource["name"],
                "address": {"value": resource["address"]},
                "remoteNetwork": {"id": resource["remoteNetworkId"]},
                "groups": {"edges": group_edges}}})

        rtnval = {"data": {"resources": {
            "edges": edges,
            "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        return rtnval

    def _handle_list_groups(self) -> Dict[str, Any]:
        """
            Build the ``groups`` query response.

            :returns: The response payload.
        """
        edges = []
        for group_id in sorted(self._groups.keys()):
            group = self._groups[group_id]
            edges.append({"node": {
                "id": group["id"], "name": group["name"]}})
        rtnval = {"data": {"groups": {
            "edges": edges,
            "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        return rtnval

    def _handle_resource_create(self,
                                *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Create a resource in server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("ResourceCreate")
        resource_id = self._mint_id(prefix="R")
        record = {
            "id": resource_id,
            "name": variables["name"],
            "address": variables["address"],
            "remoteNetworkId": variables["remoteNetworkId"]}
        self._resources[resource_id] = record
        rtnval = {"data": {"resourceCreate": {
            "ok": True, "error": None,
            "entity": {
                "id": resource_id, "name": record["name"],
                "address": {"value": record["address"]},
                "remoteNetwork": {"id": record["remoteNetworkId"]}}}}}
        return rtnval

    def _handle_resource_update(self,
                                *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Update a resource in server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("ResourceUpdate")
        resource_id = variables["id"]
        record = self._resources[resource_id]
        if "name" in variables:
            record["name"] = variables["name"]
        if "address" in variables:
            record["address"] = variables["address"]
        rtnval = {"data": {"resourceUpdate": {
            "ok": True, "error": None,
            "entity": {
                "id": resource_id, "name": record["name"],
                "address": {"value": record["address"]},
                "remoteNetwork": {"id": record["remoteNetworkId"]}}}}}
        return rtnval

    def _handle_resource_delete(self,
                                *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Delete a resource from server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("ResourceDelete")
        resource_id = variables["id"]
        if resource_id in self._resources:
            del self._resources[resource_id]
        dropped = set()
        for assignment in self._assignments:
            if assignment[1] == resource_id:
                dropped.add(assignment)
        self._assignments = self._assignments - dropped
        rtnval = {"data": {"resourceDelete": {"ok": True, "error": None}}}
        return rtnval

    def _handle_group_create(self,
                             *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Create a group in server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("GroupCreate")
        group_id = self._mint_id(prefix="G")
        self._groups[group_id] = {
            "id": group_id, "name": variables["name"]}
        rtnval = {"data": {"groupCreate": {
            "ok": True, "error": None,
            "entity": {"id": group_id, "name": variables["name"]}}}}
        return rtnval

    def _handle_group_delete(self,
                             *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Delete a group from server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("GroupDelete")
        group_id = variables["id"]
        if group_id in self._groups:
            del self._groups[group_id]
        dropped = set()
        for assignment in self._assignments:
            if assignment[0] == group_id:
                dropped.add(assignment)
        self._assignments = self._assignments - dropped
        rtnval = {"data": {"groupDelete": {"ok": True, "error": None}}}
        return rtnval

    def _handle_access_add(self,
                           *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Add a resource-group assignment in server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("ResourceAccessAdd")
        edge = (variables["principalId"], variables["resourceId"])
        self._assignments.add(edge)
        rtnval = {"data": {"resourceAccessAdd": {
            "ok": True, "error": None}}}
        return rtnval

    def _handle_access_remove(self,
                              *, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
            Remove a resource-group assignment from server state.

            :param variables: The mutation variables.

            :returns: The response payload.
        """
        self.mutation_operations.append("ResourceAccessRemove")
        edge = (variables["principalId"], variables["resourceId"])
        self._assignments.discard(edge)
        rtnval = {"data": {"resourceAccessRemove": {
            "ok": True, "error": None}}}
        return rtnval
