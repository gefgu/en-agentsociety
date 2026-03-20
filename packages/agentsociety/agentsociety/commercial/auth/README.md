# `commercial/auth/` — Authentication and Authorization

> **License**: Commercial only. Not covered by the open-source license.

This directory implements multi-tenant user authentication and authorization for the hosted AgentSociety platform, built on [Casdoor](https://casdoor.org/).

---

## Features

- **API key management**: Issue, revoke, and rotate API keys per tenant.
- **JWT tokens**: Short-lived access tokens for web UI sessions.
- **Role-based access control (RBAC)**: Roles include `admin`, `researcher`, `viewer`.
- **Multi-tenancy**: Each tenant's experiments and data are fully isolated.

---

## Integration

When installed, the `webapi/` FastAPI application automatically mounts auth middleware:

```
Request → Auth middleware → Route handler
               │
         Validates API key or JWT
         Checks tenant + role permissions
```

Unauthenticated requests receive `401 Unauthorized`. Insufficient permissions receive `403 Forbidden`.

---

## Configuration

Auth settings are provided via environment variables:

```bash
CASDOOR_ENDPOINT=https://auth.example.com
CASDOOR_CLIENT_ID=agentsociety
CASDOOR_CLIENT_SECRET=...
CASDOOR_ORG_NAME=my-org
```
