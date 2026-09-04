# Stock movements and transfers

Milestone 5 makes the inventory audit log queryable and adds atomic warehouse-to-warehouse transfers.

## API

| Method | Path | Access | Behavior |
| --- | --- | --- | --- |
| `POST` | `/api/inventory/transfer` | ADMIN, WAREHOUSE_MANAGER | Move stock between warehouses |
| `GET` | `/api/stock-movements` | Any authenticated user | Filtered, paginated movement history |
| `GET` | `/api/stock-movements/{id}` | Any authenticated user | One movement with product, warehouse, and actor details |

Movement history supports free-text product/warehouse search plus product, warehouse, movement type, date range, page size, and chronological sort parameters.

## Transfer transaction

A transfer validates an active product, two distinct warehouses, a positive quantity, and sufficient available source stock. Existing inventory rows are locked in ascending warehouse-ID order. The service then:

1. Reduces source `quantity_on_hand`.
2. Increases destination `quantity_on_hand`.
3. Creates a negative `TRANSFER_OUT` movement.
4. Creates a positive `TRANSFER_IN` movement.
5. Links both movements with the same `TRANSFER` reference.
6. Commits all four writes together.

Any validation, constraint, or concurrent-insert failure rolls the entire operation back. The frontend displays the backend result but does not enforce these business rules.

## Audit behavior

Movement responses include product, warehouse, and user summaries. Receipt and adjustment records appear alongside transfers, and the model already reserves movement types for order reservations, releases, shipments, and returns.
