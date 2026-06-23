# `commercial/` — SaaS / Commercial Layer

This package contains optional SaaS features that are not part of the open-source core. It provides multi-tenant authentication, usage billing, and a hosted executor for managed simulation runs.

> **License**: The commercial sub-packages are licensed separately from the open-source core. Contact the project maintainers for access.

---

## Sub-packages

| Directory | Purpose |
|---|---|
| `auth/` | Multi-tenant authentication and authorization (API keys, JWT, RBAC) |
| `billing/` | Usage tracking, quota enforcement, and billing hooks |
| `executor/` | Hosted/cloud executor that manages simulation lifecycle on remote infrastructure |

---

## `auth/`

Provides:

- API key management for multi-tenant deployments
- JWT token issuance and validation
- Role-based access control (who can start/stop/view which experiments)
- Integration with the `webapi/` REST backend

---

## `billing/`

Tracks resource consumption (LLM tokens, agent-hours) and enforces quotas:

- Per-tenant token budgets
- Real-time usage counters updated by `LLM` wrapper hooks
- Webhook callbacks for billing events

---

## `executor/`

A remote execution backend that:

- Accepts simulation configs via the REST API
- Schedules and runs `SimulationEngine` or `IndividualEngine` on cloud infrastructure
- Streams logs and status updates back to the client
- Handles cleanup and artifact storage (results → S3)

---

## Usage

When the commercial package is installed, the `webapi/` backend automatically activates the auth middleware and billing hooks. No code changes are needed in user-facing experiment scripts.

When not installed, the framework runs in open-source mode with no authentication or billing.
