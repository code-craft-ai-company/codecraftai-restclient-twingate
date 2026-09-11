=====================================
Code Craft AI RestClient - Twingate
=====================================

The ``codecraftai-restclient-twingate`` package is a typed, aspect-driven client for the Twingate Admin API. Despite the ``restclient-`` prefix, the upstream API is **GraphQL**, not REST — Twingate publishes a single GraphQL endpoint at ``https://<your-network>.twingate.com/api/graphql/v1``. The package consumes ``codecraftai-restclient-base`` for HTTP transport (POST, session management, auth header plumbing, aspects-driven retry/timeout) and layers GraphQL query and mutation construction on top.

The package is implemented as of Milestone M3b of the VPN/cloud-provisioning plan. See the ``specs/`` folder for the Kiro-style requirements, design, and task documentation that drives that work.

Highlights
==========

- ``TwingateClient(RestClientBase)`` exposing api groups for ``resources``, ``groups``, ``connectors``, ``remote_networks``, and ``devices``.
- ``IVPNControlPlane`` Protocol conformance via an idempotent three-phase RBAC apply (``apply_acl`` translates Tailscale-shaped flat-ACL JSON into Twingate's resource × group × assignment surface).
- Typed query and mutation builders under ``queries/`` and ``mutations/``, INPUT_OBJECT types under ``inputs/``, and ``SchemaObject`` DTOs under ``model/``.
- Bearer auth from ``TwingateServiceAccountCredential``; endpoint URL derived from the credential's network slug.
- Connector-name → connector-id resolution for ``mint_authkey`` so callers can pass tag-shaped inputs and have them work against Twingate's id-keyed surface.
- Replaces the M3-landed ``codecraftai-interop/vpn/twingate/twingatecontrolplane.py``, which becomes a re-export shim for one release cycle after this package ships.

Schema Regeneration
===================

The typed builders and DTOs are **hand-authored** from the documented Twingate GraphQL surface — see the "Codegen Decision" section of ``AGENTS.md``. A maintainer with a live Twingate network can re-sync the checked-in schema snapshot:

.. code-block:: bash

   python -m ccai.restclient.twingate._codegen.import_schema \
       --network <slug> --token <api-token>

This rewrites ``source/packages/ccai/restclient/twingate/_spec/schema.json`` and ``_spec/schema.sha256``. The emitter in ``_codegen/emitter.py`` can then validate or extend the hand-authored ``model/`` / ``inputs/`` modules. On a non-200 response or GraphQL ``errors`` the importer raises ``ConfigurationError`` and leaves the checked-in schema untouched.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/ccai/restclient/twingate/`` - Package source code (lands in M3b).
- ``source/testroots/testbase/ccai/tests/restclient/twingate/`` - TestBase test roots (lands in M3b).
- ``specs/`` - Requirements, design, and task documentation (Kiro-style).
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Tests land in Milestone M3b. Once source code is in place:

.. code-block:: bash

   source .venv/bin/activate
   testbase testing run --root ./source/testroots/testbase --includes=testbase.ccai.tests

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Codegen decision rule: workspace ``PLAN-VPN-AND-CLOUD-PROVISIONING.md`` §9.2a
