# ADR 0006: Lock transfer balances in deterministic warehouse order

## Status

Accepted

## Decision

Warehouse transfers select existing source and destination inventory rows for update in ascending warehouse-ID order, regardless of transfer direction. Both balance changes and the paired transfer movements commit in one transaction.

The two movements share a transfer reference: the `TRANSFER_OUT` movement ID becomes the `reference_id` for both records. This reuses the existing audit schema while transfers remain an inventory command rather than a separately managed aggregate.

## Consequences

- Opposite-direction transfers request the same row locks in the same order, reducing deadlock risk.
- Insufficient stock cannot produce a partial destination increase or an incomplete movement pair.
- A transfer can be reconstructed efficiently through its indexed reference fields.
- Concurrent creation of a previously absent destination balance can still return `INVENTORY_CONFLICT`; generalized retry and stress testing remains Milestone 8 work.
