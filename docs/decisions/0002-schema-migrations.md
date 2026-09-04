# ADR 0002: Alembic owns schema evolution

- Status: Accepted
- Date: 2026-09-04

## Context

Automatic ORM table creation cannot safely describe reviewed, repeatable upgrades across environments.

## Decision

All database schema changes use Alembic revisions. Containers run `alembic upgrade head` before the API starts. ORM metadata supports migration generation but the application never creates production tables directly.

## Consequences

Schema history is reviewable and deployable. Developers must include a migration with each model change and consider downgrade safety explicitly.

