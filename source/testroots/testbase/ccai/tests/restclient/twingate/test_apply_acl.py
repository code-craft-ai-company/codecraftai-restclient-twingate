"""
    Tests for the twingate-restclient three-phase idempotent apply_acl:
    - happy-path three-phase apply against a stateful fake server
    - second-apply idempotence (zero mutations)
    - input order-independence
    - malformed input -> SemanticError, no mutation runs

    Hypothesis property tests cover idempotence and order-independence.
"""

import copy

from ccai import testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.errors.exceptions import SemanticError

from ccai.restclient.twingate.acltranslator.parser import (
    parse_acl_document
)
from ccai.restclient.twingate.acltranslator.differ import build_apply_plan
from ccai.restclient.twingate.twingateclient import TwingateClient

from .twingatetestsupport import (
    make_credential, no_pause_aspects
)
from .fakegraphqlserver import (
    FakeGraphQLServer
)


def _make_acl_client(server: FakeGraphQLServer) -> TwingateClient:
    client = TwingateClient(credential=make_credential())
    client._session = server
    return client


def _sample_acl() -> dict:
    rtnval = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {
            "db": "db.acme.internal",
            "web": "web.acme.internal",
        },
        "groups": {
            "engineering": ["alice"],
            "ops": ["bob"],
        },
        "acls": [
            {"action": "accept", "src": ["engineering"],
             "dst": ["db:5432", "web:443"]},
            {"action": "accept", "src": ["ops"], "dst": ["db"]},
        ],
    }
    return rtnval


# ----------------------------------------------------------------------
# TestApplyAclHappyPath
# ----------------------------------------------------------------------


def test_three_phase_apply_on_empty_network() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)

    client.apply_acl(acl_doc=_sample_acl(), aspects=no_pause_aspects())

    # 2 resources + 2 groups + 3 assignment edges.
    resource_creates = server.mutation_operations.count("ResourceCreate")
    group_creates = server.mutation_operations.count("GroupCreate")
    access_adds = server.mutation_operations.count("ResourceAccessAdd")
    testbase.assert_equal(resource_creates, 2)
    testbase.assert_equal(group_creates, 2)
    testbase.assert_equal(access_adds, 3)
    return

def test_phase_order_resources_then_groups_then_edges() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    client.apply_acl(acl_doc=_sample_acl(), aspects=no_pause_aspects())

    ops = server.mutation_operations
    last_resource = max(
        i for i, o in enumerate(ops) if o == "ResourceCreate")
    first_group = min(
        i for i, o in enumerate(ops) if o == "GroupCreate")
    last_group = max(
        i for i, o in enumerate(ops) if o == "GroupCreate")
    first_edge = min(
        i for i, o in enumerate(ops) if o == "ResourceAccessAdd")
    testbase.assert_lessthan(last_resource, first_group)
    testbase.assert_lessthan(last_group, first_edge)
    return

def test_update_phase_on_address_change() -> None:
    server = FakeGraphQLServer()
    server.seed_resource(
        name="db", address="OLD.address", remote_network_id="RN1")
    client = _make_acl_client(server)

    acl = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {"db": "db.acme.internal"},
        "groups": {}, "acls": [],
    }
    client.apply_acl(acl_doc=acl, aspects=no_pause_aspects())
    testbase.assert_equal(
        server.mutation_operations.count("ResourceUpdate"), 1)
    testbase.assert_equal(
        server.mutation_operations.count("ResourceCreate"), 0)
    return

def test_delete_phase_for_undesired_resource() -> None:
    server = FakeGraphQLServer()
    server.seed_resource(
        name="stale", address="stale.local", remote_network_id="RN1")
    client = _make_acl_client(server)

    acl = {"twingate": {"remote_network_id": "RN1"},
           "hosts": {}, "groups": {}, "acls": []}
    client.apply_acl(acl_doc=acl, aspects=no_pause_aspects())
    testbase.assert_equal(
        server.mutation_operations.count("ResourceDelete"), 1)
    return


# ----------------------------------------------------------------------
# TestApplyAclIdempotence
# ----------------------------------------------------------------------


def test_second_apply_issues_zero_mutations() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)

    client.apply_acl(acl_doc=_sample_acl(), aspects=no_pause_aspects())
    first_count = len(server.mutation_operations)
    testbase.assert_greater(first_count, 0)

    server.mutation_operations.clear()
    client.apply_acl(acl_doc=_sample_acl(), aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return


# ----------------------------------------------------------------------
# TestApplyAclOrderIndependence
# ----------------------------------------------------------------------


def test_input_order_does_not_change_final_state() -> None:
    server_a = FakeGraphQLServer()
    client_a = _make_acl_client(server_a)
    client_a.apply_acl(
        acl_doc=_sample_acl(), aspects=no_pause_aspects())

    # Reverse every list/dict ordering in the document.
    shuffled = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {
            "web": "web.acme.internal",
            "db": "db.acme.internal",
        },
        "groups": {
            "ops": ["bob"],
            "engineering": ["alice"],
        },
        "acls": [
            {"action": "accept", "src": ["ops"], "dst": ["db"]},
            {"action": "accept", "src": ["engineering"],
             "dst": ["web:443", "db:5432"]},
        ],
    }
    server_b = FakeGraphQLServer()
    client_b = _make_acl_client(server_b)
    client_b.apply_acl(
        acl_doc=shuffled, aspects=no_pause_aspects())

    testbase.assert_equal(
        sorted(server_a.mutation_operations),
        sorted(server_b.mutation_operations))
    return


# ----------------------------------------------------------------------
# TestApplyAclMalformed
# ----------------------------------------------------------------------


def test_none_acl_raises_semantic_error() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    with testbase.raises(SemanticError):
        client.apply_acl(acl_doc=None, aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return

def test_non_dict_acl_raises() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    with testbase.raises(SemanticError):
        client.apply_acl(
            acl_doc=["not", "a", "dict"], aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return

def test_acl_referencing_undeclared_host_raises() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    acl = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {"db": "db.local"},
        "groups": {"eng": []},
        "acls": [{"action": "accept", "src": ["eng"],
                  "dst": ["ghost"]}],
    }
    with testbase.raises(SemanticError):
        client.apply_acl(acl_doc=acl, aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return

def test_acl_referencing_undeclared_group_raises() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    acl = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {"db": "db.local"},
        "groups": {},
        "acls": [{"action": "accept", "src": ["ghostgroup"],
                  "dst": ["db"]}],
    }
    with testbase.raises(SemanticError):
        client.apply_acl(acl_doc=acl, aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return

def test_malformed_hosts_block_raises() -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)
    acl = {"hosts": "should-be-a-mapping", "groups": {}, "acls": []}
    with testbase.raises(SemanticError):
        client.apply_acl(acl_doc=acl, aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return


# ----------------------------------------------------------------------
# Property tests (hypothesis)
# ----------------------------------------------------------------------


_HOST_NAMES = ["db", "web", "cache", "api", "queue"]
_GROUP_NAMES = ["eng", "ops", "sec", "data"]


def _acl_strategy():
    host_subset = st.lists(
        st.sampled_from(_HOST_NAMES), min_size=1, max_size=4, unique=True)
    group_subset = st.lists(
        st.sampled_from(_GROUP_NAMES), min_size=1, max_size=3, unique=True)
    return st.builds(_build_acl_doc, host_subset, group_subset)


def _build_acl_doc(hosts: list, groups: list) -> dict:
    rtnval = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": {h: f"{h}.acme.internal" for h in hosts},
        "groups": {g: [] for g in groups},
        "acls": [
            {"action": "accept", "src": [groups[0]],
             "dst": [hosts[0]]},
        ],
    }
    return rtnval


# ----------------------------------------------------------------------
# TestApplyAclProperties
# ----------------------------------------------------------------------


@given(_acl_strategy(), constraints={"max_examples": 60})
def test_apply_is_idempotent(acl_doc: dict) -> None:
    server = FakeGraphQLServer()
    client = _make_acl_client(server)

    client.apply_acl(
        acl_doc=copy.deepcopy(acl_doc), aspects=no_pause_aspects())
    server.mutation_operations.clear()
    client.apply_acl(
        acl_doc=copy.deepcopy(acl_doc), aspects=no_pause_aspects())
    testbase.assert_equal(server.mutation_operations, [])
    return

@given(_acl_strategy(), constraints={"max_examples": 60})
def test_apply_is_order_independent(acl_doc: dict) -> None:
    # Build a re-ordered variant: reverse hosts, groups, and the
    # dst list inside the single rule.
    reordered = {
        "twingate": {"remote_network_id": "RN1"},
        "hosts": dict(reversed(list(acl_doc["hosts"].items()))),
        "groups": dict(reversed(list(acl_doc["groups"].items()))),
        "acls": acl_doc["acls"],
    }

    server_a = FakeGraphQLServer()
    client_a = _make_acl_client(server_a)
    client_a.apply_acl(
        acl_doc=copy.deepcopy(acl_doc), aspects=no_pause_aspects())

    server_b = FakeGraphQLServer()
    client_b = _make_acl_client(server_b)
    client_b.apply_acl(
        acl_doc=reordered, aspects=no_pause_aspects())

    testbase.assert_equal(
        sorted(server_a.mutation_operations),
        sorted(server_b.mutation_operations))
    return

@given(_acl_strategy(), constraints={"max_examples": 60})
def test_differ_plan_empty_when_state_matches(
        acl_doc: dict) -> None:
    # Parsing the same document twice and diffing the second parse
    # against the first parse's projected state yields no mutations.
    desired = parse_acl_document(
        acl_doc=acl_doc, default_remote_network_id="RN1")

    from ccai.restclient.twingate.model.twingateresource import (
        TwingateResource
    )
    from ccai.restclient.twingate.model.twingategroup import (
        TwingateGroup
    )

    current_resources = [
        TwingateResource(
            resource_id=f"R{i}", name=r.name, address=r.address,
            remote_network_id=r.remote_network_id, protocols={})
        for i, r in enumerate(desired.resources)]
    current_groups = [
        TwingateGroup(group_id=f"G{i}", name=g.name, user_ids=[])
        for i, g in enumerate(desired.groups)]

    plan = build_apply_plan(
        desired=desired,
        current_resources=current_resources,
        current_groups=current_groups,
        current_edges=desired.edges)
    testbase.assert_true(plan.is_empty())
    return
