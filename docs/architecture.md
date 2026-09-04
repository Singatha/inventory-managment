# Architecture

## Current delivery

Milestone 1 established the runnable vertical slice. Milestone 2 added identity and access control, Milestone 3 added the product catalog, and Milestone 4 introduced warehouse inventory. Milestone 5 completes the core stock flow with atomic warehouse transfers and a queryable movement audit trail. Inventory services own transaction boundaries and persist balance changes with their audit movements atomically.

## System context

```mermaid
flowchart TB
    User[Warehouse user] --> Web[React + Ant Design]
    Web -->|HTTPS REST| Backend[FastAPI modular monolith]
    Backend --> Database[(PostgreSQL)]
    Backend -. Milestone 9 .-> Broker[(RabbitMQ)]
    Broker -. Milestone 9 .-> Workers[Idempotent workers]
```

## Backend boundaries

Each feature package will own its routes, schemas, service rules, and persistence models where practical. Shared technical code belongs in `core`; shared API behavior belongs in `common`.

```mermaid
flowchart LR
    Route[API route] --> Schema[Pydantic validation]
    Schema --> Service[Feature service]
    Service --> Repository[SQLAlchemy persistence]
    Repository --> PostgreSQL[(PostgreSQL)]
```

Routes stay thin. Services define transaction boundaries for inventory workflows, and repositories centralize allowlisted sorting, aggregate queries, and locking reads. Inventory mutation services use PostgreSQL row locks for existing balances and commit balance changes plus movement records together. Transfers request locks in warehouse-ID order so opposite-direction operations use the same lock order.

## Frontend boundaries

Routes map to feature pages inside the shared application layout. Axios owns HTTP transport and TanStack Query owns server-state caching. Ant Design supplies standard interface primitives. Client-side rules improve usability but never authorize a domain transition.

## Key tradeoff: modular monolith first

A modular monolith provides one database transaction across orders and inventory, simple local operations, and fewer distributed failure modes. Feature packages preserve seams that could support later extraction, but extraction is not a goal until independent scaling or ownership demands it.
