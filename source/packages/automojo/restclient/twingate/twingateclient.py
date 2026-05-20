"""
    .. module:: twingateclient
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`TwingateClient` typed,
                   aspect-driven GraphQL client for the Twingate Admin API
                   that implements the :class:`IVPNControlPlane` protocol.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import json
import logging
import os

from http import HTTPStatus
from typing import Any, Dict, List, Optional

from requests import Response, Session

from automojo.credentials.basecredential import BaseCredential
from automojo.credentials.twingateserviceaccountcredential import (
    TwingateServiceAccountCredential
)
from automojo.errors.exceptions import ConfigurationError, SemanticError
from automojo.interfaces.ivpncontrolplane import VPNDeviceRecord

from automojo.restclient.base.restclientbase import RestClientBase

from automojo.restclient.twingate.aspectstwingate import (
    AspectsTwingate, DEFAULT_TWINGATE_ASPECTS
)
from automojo.restclient.twingate.apigroups.resourcesgroup import ResourcesGroup
from automojo.restclient.twingate.apigroups.groupsgroup import GroupsGroup
from automojo.restclient.twingate.apigroups.connectorsgroup import ConnectorsGroup
from automojo.restclient.twingate.apigroups.remotenetworksgroup import (
    RemoteNetworksGroup
)
from automojo.restclient.twingate.apigroups.devicesgroup import DevicesGroup
from automojo.restclient.twingate.apigroups.graphqlsupport import (
    require_mutation_result
)
from automojo.restclient.twingate.acltranslator.parser import parse_acl_document
from automojo.restclient.twingate.acltranslator.differ import build_apply_plan
from automojo.restclient.twingate.acltranslator.executor import (
    execute_apply_plan
)
from automojo.restclient.twingate.exceptions import (
    VPNControlPlaneACLError, VPNControlPlaneAuthKeyError,
    VPNControlPlaneQueryError
)
from automojo.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from automojo.restclient.twingate.mutations.build_resourceaccess_mutations import (
    build_resourceaccessadd, build_resourceaccessremove
)


GRAPHQL_LEAF = "/api/graphql/v1"


class TwingateClient(RestClientBase):
    """
        :class:`TwingateClient` is a :class:`RestClientBase` subclass that
        POSTs typed GraphQL bodies to the Twingate Admin API and implements
        the :class:`IVPNControlPlane` protocol.

        HONESTY WARNING — Twingate diverges from the Tailscale-shaped
        intent of :class:`IVPNControlPlane` in three places:

        - ``mint_authkey`` — Twingate has no flat auth-key mint flow. The
          method treats ``tags[0]`` as a connector NAME, resolves it to a
          connector ID, then issues ``connectorGenerateTokens``. Twingate
          connector tokens are neither reusable nor ephemeral and have a
          provider-fixed lifetime, so ``reusable``, ``ephemeral`` and
          ``ttl_seconds`` are NOT honoured — supplying more than one tag is
          rejected with :class:`SemanticError`.
        - ``apply_acl`` — Twingate has NO flat-ACL primitive. The method is
          a translation, not a faithful representation: it parses a
          Tailscale-shaped flat-ACL document and converges the network to
          the equivalent Twingate resource × group × assignment state in
          three idempotent phases.
        - ``list_devices`` — Twingate ``Device`` nodes carry no overlay
          address, so every returned :class:`VPNDeviceRecord` has
          ``overlay_address=None``.

        The GraphQL endpoint URL is derived from the credential's network
        slug: ``https://<slug>.twingate.com/api/graphql/v1``.
    """

    def __init__(self, *, credential: TwingateServiceAccountCredential,
                 host: Optional[str] = None,
                 aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS):
        """
            Initialize the Twingate GraphQL client.

            :param credential: A :class:`TwingateServiceAccountCredential`.
                The ``network_slug`` field determines the default host
                (``<slug>.twingate.com``); the ``api_token`` is sent as a
                ``Bearer`` header.
            :param host: Optional explicit host override (useful for tests).
            :param aspects: Default :class:`AspectsTwingate` for calls.

            :returns: ``None``.

            :raises: :class:`ConfigurationError` when ``credential`` is
                ``None`` or is any other :class:`BaseCredential` subclass.
        """
        if credential is None:
            err_msg_lines = [
                "TwingateClient requires a TwingateServiceAccountCredential.",
                "No credential was supplied.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        if not isinstance(credential, TwingateServiceAccountCredential):
            err_msg_lines = [
                "TwingateClient requires a TwingateServiceAccountCredential.",
                f"FOUND CREDENTIAL TYPE: {type(credential).__name__}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        host_value = host
        if host_value is None:
            host_value = f"{credential.network_slug}.twingate.com"

        super().__init__(
            host=host_value,
            credential=credential,
            scheme="https",
            aspects=aspects,
        )

        self._resources = ResourcesGroup(self)
        self._groups = GroupsGroup(self)
        self._connectors = ConnectorsGroup(self)
        self._remote_networks = RemoteNetworksGroup(self)
        self._devices = DevicesGroup(self)
        self._logger = logging.getLogger(__name__)
        return

    @property
    def resources(self) -> ResourcesGroup:
        """
            Return the resources api group.

            :returns: A :class:`ResourcesGroup`.
        """
        rtnval = self._resources
        return rtnval

    @property
    def groups(self) -> GroupsGroup:
        """
            Return the groups api group.

            :returns: A :class:`GroupsGroup`.
        """
        rtnval = self._groups
        return rtnval

    @property
    def connectors(self) -> ConnectorsGroup:
        """
            Return the connectors api group.

            :returns: A :class:`ConnectorsGroup`.
        """
        rtnval = self._connectors
        return rtnval

    @property
    def remote_networks(self) -> RemoteNetworksGroup:
        """
            Return the remote-networks api group.

            :returns: A :class:`RemoteNetworksGroup`.
        """
        rtnval = self._remote_networks
        return rtnval

    @property
    def devices(self) -> DevicesGroup:
        """
            Return the devices api group.

            :returns: A :class:`DevicesGroup`.
        """
        rtnval = self._devices
        return rtnval

    def authenticate(self) -> None:
        """
            Establish the :class:`Session` used for GraphQL calls. Sets the
            ``Authorization: Bearer <token>`` and ``X-Network-Slug`` headers
            from the :class:`TwingateServiceAccountCredential`.

            :returns: ``None``.
        """
        credential: TwingateServiceAccountCredential = self._credential

        session = Session()
        session.verify = self._verify_certificate
        session.headers.update({
            "Authorization": f"Bearer {credential.api_token}",
            "X-Network-Slug": credential.network_slug,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        self._session = session
        return None

    def graphql_call(self, *, body: GraphQLRequestBody,
                     aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Dict[str, Any]:
        """
            POST a typed GraphQL request body to the Twingate endpoint and
            return the decoded JSON payload.

            :param body: A :class:`GraphQLRequestBody` produced by a typed
                builder.
            :param aspects: Behaviour control for the call.

            :returns: The decoded GraphQL response payload as a dictionary.

            :raises: :class:`VPNControlPlaneQueryError` when the response
                body is not valid JSON.
        """
        payload_dict = body.as_payload()
        encoded_body = json.dumps(payload_dict).encode("utf-8")

        operation_name = body.operation_name
        if operation_name is None:
            operation_name = "<unspecified>"
        context_msg = f"twingate-graphql:{operation_name}"

        resp: Response = self.perform_call(
            leaf=GRAPHQL_LEAF,
            method="POST",
            params=None,
            body=encoded_body,
            exp_status=HTTPStatus.OK,
            headers=None,
            context_msg=context_msg,
            aspects=aspects,
        )

        try:
            decoded = resp.json()
        except ValueError as decode_err:
            resp_text = ""
            if resp.text is not None:
                resp_text = resp.text[:512]
            err_msg_lines = [
                "Twingate GraphQL response was not valid JSON.",
                f"OPERATION: {operation_name}",
                f"STATUS: {resp.status_code}",
                f"BODY: {resp_text}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneQueryError(
                err_msg,
                response_body=resp.text,
                status_code=resp.status_code,
            ) from decode_err

        rtnval = decoded
        return rtnval

    def resource_access_add(self, *, group_id: str, resource_id: str,
                            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Issue a ``resourceAccessAdd`` mutation binding a group to a
            resource.

            :param group_id: Provider-assigned group identifier.
            :param resource_id: Provider-assigned resource identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_resourceaccessadd(
            group_id=group_id, resource_id=resource_id)
        payload = self.graphql_call(body=request_body, aspects=aspects)
        require_mutation_result(
            payload=payload, mutation_name="resourceAccessAdd",
            acl_phase=True)
        return None

    def resource_access_remove(self, *, group_id: str, resource_id: str,
                               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Issue a ``resourceAccessRemove`` mutation removing a group from
            a resource.

            :param group_id: Provider-assigned group identifier.
            :param resource_id: Provider-assigned resource identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneACLError`.
        """
        request_body = build_resourceaccessremove(
            group_id=group_id, resource_id=resource_id)
        payload = self.graphql_call(body=request_body, aspects=aspects)
        require_mutation_result(
            payload=payload, mutation_name="resourceAccessRemove",
            acl_phase=True)
        return None

    # ------------------------------------------------------------------
    # IVPNControlPlane methods
    # ------------------------------------------------------------------

    def mint_authkey(self, *, reusable: bool, ephemeral: bool,
                     tags: List[str], ttl_seconds: int,
                     aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> str:
        """
            Mint a Twingate connector token bundle.

            HONESTY WARNING — Twingate has no flat auth-key mint flow.
            ``tags[0]`` is interpreted as a connector NAME; it is resolved
            against ``connectors.list()`` and the resolved id is passed to
            ``connectorGenerateTokens``. ``reusable``, ``ephemeral`` and
            ``ttl_seconds`` are accepted for protocol conformance but NOT
            honoured — Twingate connector tokens have a provider-fixed
            lifetime. Supplying more than one tag is rejected because a
            connector token is scoped to exactly one connector.

            :param reusable: Accepted for protocol conformance; unused.
            :param ephemeral: Accepted for protocol conformance; unused.
            :param tags: Connector identity. ``tags[0]`` is the connector
                name; exactly one tag is required.
            :param ttl_seconds: Accepted for protocol conformance; unused.
            :param aspects: Behaviour control for the call.

            :returns: The combined ``"<accessToken>:<refreshToken>"``
                string.

            :raises: :class:`SemanticError` when ``tags`` is empty or holds
                more than one entry.
            :raises: :class:`VPNControlPlaneAuthKeyError` when the connector
                name does not resolve.
        """
        if tags is None or len(tags) == 0:
            err_msg_lines = [
                "Twingate mint_authkey requires a connector identity.",
                "The 'tags' parameter must contain exactly one entry (the "
                "connector name).",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        if len(tags) > 1:
            err_msg_lines = [
                "Twingate connector tokens are scoped to a single "
                "connector.",
                "The 'tags' parameter must contain exactly one entry.",
                f"FOUND TAGS: {tags}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        connector_name = tags[0]
        connector_id = self._resolve_connector_id_by_name(
            name=connector_name, aspects=aspects)

        tokens = self._connectors.generate_tokens(
            connector_id=connector_id, aspects=aspects)

        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        rtnval = f"{access_token}:{refresh_token}"
        return rtnval

    def list_devices(self, *,
                     aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[VPNDeviceRecord]:
        """
            Enumerate Twingate ``Device`` nodes as :class:`VPNDeviceRecord`
            entries.

            HONESTY WARNING — Twingate devices carry no overlay address, so
            every record has ``overlay_address=None``. Twingate does not
            attach free-form tags to devices, so ``tags`` is always empty.

            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`VPNDeviceRecord` entries.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        devices = self._devices.list(aspects=aspects)

        results: List[VPNDeviceRecord] = []
        for device in devices:
            last_seen: Optional[str] = None
            if device.last_connected_at is not None and len(device.last_connected_at) > 0:
                last_seen = device.last_connected_at

            os_value: Optional[str] = None
            if device.os_name is not None and len(device.os_name) > 0:
                os_value = device.os_name

            record = VPNDeviceRecord(
                device_id=device.device_id,
                hostname=device.name,
                overlay_address=None,
                tags=[],
                os=os_value,
                last_seen=last_seen,
            )
            results.append(record)

        rtnval = results
        return rtnval

    def delete_device(self, *, device_id: str,
                      aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            De-register a Twingate device by identifier. The call is a
            no-op when the device is already absent (idempotent contract).

            :param device_id: Provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneMutationError` for any error
                other than not-found.
        """
        self._devices.delete(device_id=device_id, aspects=aspects)
        return None

    def apply_acl(self, *, acl_doc: dict,
                  aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Apply a Tailscale-shaped flat-ACL document to the Twingate
            network through an idempotent three-phase RBAC translation.

            HONESTY WARNING — Twingate has NO flat-ACL primitive. This
            method is a translation, not a faithful representation. The
            Tailscale-shaped document is parsed into a provider-neutral
            intermediate model; the model is set-diffed against the current
            Twingate state; and the resulting plan is executed in three
            phases — (1) resources, (2) groups, (3) resource-group
            assignments — pausing ``mutation_dependency_pause_seconds``
            between dependent phases.

            Idempotence — applying the same document twice issues zero
            mutations on the second call because the set-diff produces
            empty phases when the network already matches.

            :param acl_doc: A Tailscale-shaped flat-ACL JSON document
                exposing ``hosts``, ``groups`` and ``acls``. An optional
                top-level ``twingate`` block may carry
                ``remote_network_id`` used as the parent network for every
                derived resource.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`SemanticError` when ``acl_doc`` is malformed;
                no mutation runs in that case.
            :raises: :class:`VPNControlPlaneACLError` when a phase fails.
        """
        default_remote_network_id = ""
        if isinstance(acl_doc, dict):
            twingate_block = acl_doc.get("twingate")
            if isinstance(twingate_block, dict):
                candidate = twingate_block.get("remote_network_id", "")
                if isinstance(candidate, str):
                    default_remote_network_id = candidate

        # Parse first — malformed input raises SemanticError before any
        # network read or mutation runs.
        desired = parse_acl_document(
            acl_doc=acl_doc,
            default_remote_network_id=default_remote_network_id)

        current_resources = self._resources.list(aspects=aspects)
        current_groups = self._groups.list(aspects=aspects)
        current_edges = self._resources.iter_assignments(aspects=aspects)

        plan = build_apply_plan(
            desired=desired,
            current_resources=current_resources,
            current_groups=current_groups,
            current_edges=current_edges)

        resources_by_name = {}
        for resource in current_resources:
            resources_by_name[resource.name] = resource

        groups_by_name = {}
        for group in current_groups:
            groups_by_name[group.name] = group

        execute_apply_plan(
            plan=plan,
            resources=self._resources,
            groups=self._groups,
            access=self,
            resources_by_name=resources_by_name,
            groups_by_name=groups_by_name,
            aspects=aspects)

        return None

    def _resolve_connector_id_by_name(self, *, name: str,
                                      aspects: AspectsTwingate) -> str:
        """
            Resolve a connector identifier from its display name by listing
            existing connectors.

            :param name: Display name of the connector.
            :param aspects: Behaviour control for the call.

            :returns: The provider-assigned connector identifier.

            :raises: :class:`VPNControlPlaneAuthKeyError` when no connector
                or more than one connector with the supplied name exists.
        """
        connectors = self._connectors.list(aspects=aspects)

        matched_ids: List[str] = []
        for connector in connectors:
            if connector.name == name:
                matched_ids.append(connector.connector_id)

        if len(matched_ids) == 0:
            err_msg_lines = [
                "Twingate connector lookup by name returned no match.",
                f"NAME: {name}",
                f"AVAILABLE: {[c.name for c in connectors]}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(err_msg)

        if len(matched_ids) > 1:
            err_msg_lines = [
                "Twingate connector lookup by name was ambiguous.",
                f"NAME: {name}",
                f"MATCHED IDS: {matched_ids}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneAuthKeyError(err_msg)

        rtnval = matched_ids[0]
        return rtnval


__all__ = ["TwingateClient", "GRAPHQL_LEAF"]
