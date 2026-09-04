# ADR 0005: Commit inventory balances and audit movements together

## Status

Accepted

## Decision

Every inventory mutation updates the inventory balance and inserts its stock movement inside one PostgreSQL transaction. Existing inventory rows are selected with a row-level update lock before their quantities are changed. Available quantity remains a computed value rather than a stored column.

## Consequences

- A successful response guarantees both the balance and its audit evidence were persisted.
- A failure rolls back both records, avoiding unaudited stock changes.
- Database constraints provide a final guard against invalid negative or over-reserved balances.
- Concurrent creation of a new product/warehouse pair may return an `INVENTORY_CONFLICT`; stronger retry and concurrency coverage is planned for Milestone 8.
- The same transaction pattern can expand to two-sided transfers, reservations, shipments, and returns.
