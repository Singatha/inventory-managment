# ADR 0003: JWT bearer sessions for the SPA

- Status: Accepted with future hardening
- Date: 2026-09-04

## Context

StockFlow needs API authentication that works for its React client and documents cleanly through OpenAPI. Roles can change while a token is still valid, and deactivated users must lose access promptly.

## Decision

Issue short-lived signed access tokens and longer-lived refresh tokens. Tokens carry identity, role, type, expiry, and a unique ID. Protected requests verify the token and reload the user from PostgreSQL, making the database authoritative for role and active status. New registrations are always employees; an environment-driven bootstrap creates the initial administrator.

## Consequences

The API remains stateless with straightforward bearer authorization, but database lookup still occurs on protected requests. Browser local storage is acceptable for this development milestone but has XSS exposure. Before production, move refresh tokens to HttpOnly cookies and add a revocation or token-version strategy for logout-all-sessions and credential changes.

