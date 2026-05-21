"""
    .. module:: test_reauth_on_401
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Regression tests for the Twingate GraphQL client
                   mint-once-retry on an HTTP 401 from a real API call
                   (audit RC-H2). An expired token must trigger exactly one
                   transparent re-authentication; a second 401 must surface
                   as a :class:`TwingateAuthError`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import json
import unittest

from typing import Any, List

from automojo.restclient.twingate.exceptions import TwingateAuthError

from automojo.tests.restclient.twingate.twingatetestsupport import (
    FakeResponse, make_credential, no_pause_aspects
)
from automojo.restclient.twingate.twingateclient import TwingateClient


class StatusScriptedSession:
    """
        Scripted fake session whose responses carry a per-call status
        code, used to exercise the 401 mint-once-retry path.
    """

    def __init__(self, *, scripted: List[Any]):
        """
            Initialize the scripted session.

            :param scripted: Ordered ``(status_code, payload)`` tuples;
                each :meth:`send` call consumes one entry.

            :returns: ``None``.
        """
        self.verify = True
        self.headers = {}
        self._scripted = list(scripted)
        self.send_count = 0
        return

    def prepare_request(self, request: Any) -> Any:
        """
            Echo the request back unchanged.

            :param request: The request being prepared.

            :returns: The same request object.
        """
        return request

    def send(self, prepared_request: Any, **kwargs: Any) -> FakeResponse:
        """
            Pop the next scripted ``(status, payload)`` and build a
            response.

            :param prepared_request: The prepared request.
            :param kwargs: Ignored transport keyword arguments.

            :returns: A :class:`FakeResponse`.
        """
        self.send_count = self.send_count + 1
        status_code, payload = self._scripted.pop(0)
        rtnval = FakeResponse(status_code=status_code, payload=payload)
        return rtnval


def _make_client(*, scripted: List[Any]) -> TwingateClient:
    """
        Build a :class:`TwingateClient` bound to a status-scripted fake
        session; ``authenticate`` is stubbed so a re-auth keeps the fake.

        :param scripted: Ordered ``(status, payload)`` tuples.

        :returns: A :class:`TwingateClient` ready for offline testing.
    """
    client = TwingateClient(credential=make_credential())
    session = StatusScriptedSession(scripted=scripted)

    def fake_authenticate() -> None:
        client._session = session
        return None

    client.authenticate = fake_authenticate
    client._session = session
    rtnval = client
    return rtnval


class TestReauthOn401(unittest.TestCase):

    def test_401_then_200_retries_once(self) -> None:
        """
            A 401 followed by a 200 must yield the 200 payload after
            exactly one re-auth (two HTTP sends total).
        """
        ok_payload = {"data": {"devices": {"edges": [],
                      "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        scripted = [
            (401, {"errors": [{"message": "token expired"}]}),
            (200, ok_payload),
        ]
        client = _make_client(scripted=scripted)

        devices = client.list_devices(aspects=no_pause_aspects())

        self.assertEqual(devices, [])
        self.assertEqual(client._session.send_count, 2)
        return

    def test_persistent_401_raises_auth_error(self) -> None:
        """
            Two consecutive 401 responses must surface as a
            :class:`TwingateAuthError` — the retry is attempted at most
            once.
        """
        scripted = [
            (401, {"errors": [{"message": "token expired"}]}),
            (401, {"errors": [{"message": "token expired"}]}),
        ]
        client = _make_client(scripted=scripted)

        with self.assertRaises(TwingateAuthError):
            client.list_devices(aspects=no_pause_aspects())

        self.assertEqual(client._session.send_count, 2)
        return


if __name__ == "__main__":
    unittest.main()
