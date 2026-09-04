# ADR 0001: Begin with a modular monolith

- Status: Accepted
- Date: 2026-09-04

## Context

Inventory reservation, transfers, shipping, and purchase-order receipt require strong transactional consistency. Starting with independently deployed services would introduce distributed transactions and operational overhead before the domain is proven.

## Decision

Use one FastAPI deployment and one PostgreSQL database, organized into explicit feature packages. Add asynchronous messaging only for post-commit events and background reactions after the synchronous core works.

## Consequences

Cross-feature workflows can use ordinary database transactions and local development remains simple. Feature boundaries require discipline rather than network enforcement. A feature can be extracted later if scaling, availability, or team ownership gives a concrete reason.

