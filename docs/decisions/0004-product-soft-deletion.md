# ADR 0004: Soft-delete products

- Status: Accepted
- Date: 2026-09-04

## Context

Products will be referenced by inventory, stock movements, orders, and purchase orders. Physically deleting a product would either break those references or erase useful operational context.

## Decision

The product delete endpoint sets `is_active` to false. Inactive products remain directly addressable and can be included through explicit list filters. Managers may reactivate them through the update endpoint.

## Consequences

Historical references stay intact and accidental deletion is reversible. Queries that represent selectable products must explicitly filter for active records. Storage grows with retired products, which is acceptable for this domain.

