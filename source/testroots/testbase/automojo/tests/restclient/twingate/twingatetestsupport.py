"""
    Shared test support for the Twingate REST client test suite.

    Provides a scripted fake :class:`requests.Session` so every test runs
    entirely against in-memory GraphQL responses — no live network.
"""

import json

from typing import Any, Dict, List

from automojo.credentials.twingateserviceaccountcredential import (
    TwingateServiceAccountCredential
)
from automojo.restclient.twingate.aspectstwingate import AspectsTwingate
from automojo.restclient.twingate.twingateclient import TwingateClient


def make_credential() -> TwingateServiceAccountCredential:
    """
        Build a Twingate service-account credential for tests.

        :returns: A :class:`TwingateServiceAccountCredential`.
    """
    rtnval = TwingateServiceAccountCredential(
        identifier="tg-test",
        categories=["twingate-service-account"],
        api_token="tg-svc-test-token",
        network_slug="acme",
    )
    return rtnval


def no_pause_aspects() -> AspectsTwingate:
    """
        Build an :class:`AspectsTwingate` with the mutation pause disabled
        so the three-phase apply runs without wall-clock sleeps.

        :returns: An :class:`AspectsTwingate` with
            ``mutation_dependency_pause_seconds=0``.
    """
    rtnval = AspectsTwingate(mutation_dependency_pause_seconds=0)
    return rtnval


class FakeResponse:
    """
        Minimal stand-in for :class:`requests.Response` carrying a status
        code and a JSON body.
    """

    def __init__(self, *, status_code: int, payload: Any):
        """
            Initialize the fake response.

            :param status_code: The HTTP status code to report.
            :param payload: The JSON-serialisable body.

            :returns: ``None``.
        """
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")
        self.text = json.dumps(payload)
        self.headers = {}
        return

    def json(self) -> Any:
        """
            Return the decoded JSON body.

            :returns: The payload supplied at construction time.
        """
        return self._payload


class FakeSession:
    """
        Scripted fake :class:`requests.Session`. Each call to
        :meth:`send` pops the next scripted response and records the
        prepared request for later assertions.
    """

    def __init__(self, *, scripted_payloads: List[Any],
                 status_code: int = 200):
        """
            Initialize the fake session.

            :param scripted_payloads: Ordered list of GraphQL response
                payloads. Each :meth:`send` call consumes one.
            :param status_code: The HTTP status code every response should
                report. Defaults to ``200``.

            :returns: ``None``.
        """
        self.verify = True
        self.headers: Dict[str, str] = {}
        self._scripted = list(scripted_payloads)
        self._status_code = status_code
        self.sent_requests: List[Any] = []
        self.sent_bodies: List[Dict[str, Any]] = []
        return

    def prepare_request(self, request: Any) -> Any:
        """
            Echo the request back as the prepared request.

            :param request: The :class:`requests.Request` instance.

            :returns: The same request object.
        """
        return request

    def send(self, prepared_request: Any, **kwargs: Any) -> FakeResponse:
        """
            Pop the next scripted response and record the request.

            :param prepared_request: The prepared request being sent.
            :param kwargs: Ignored transport keyword arguments.

            :returns: A :class:`FakeResponse`.
        """
        self.sent_requests.append(prepared_request)

        body = prepared_request.data
        if isinstance(body, (bytes, bytearray)):
            decoded = json.loads(body.decode("utf-8"))
        else:
            decoded = body
        self.sent_bodies.append(decoded)

        if len(self._scripted) == 0:
            payload = {"data": {}}
        else:
            payload = self._scripted.pop(0)

        rtnval = FakeResponse(status_code=self._status_code, payload=payload)
        return rtnval


def make_client(*, scripted_payloads: List[Any],
                status_code: int = 200) -> TwingateClient:
    """
        Build a :class:`TwingateClient` whose session is a scripted
        :class:`FakeSession`.

        :param scripted_payloads: Ordered GraphQL response payloads.
        :param status_code: The HTTP status code every scripted response
            should report. Defaults to ``200``.

        :returns: A :class:`TwingateClient` ready for offline testing.
    """
    client = TwingateClient(credential=make_credential())
    client._session = FakeSession(scripted_payloads=scripted_payloads,
                                  status_code=status_code)
    rtnval = client
    return rtnval
