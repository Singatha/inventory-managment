# Warehouses and inventory

Milestone 4 introduces physical warehouse locations and inventory balances for each product/warehouse pair.

## Access

| Operation | ADMIN | WAREHOUSE_MANAGER | EMPLOYEE |
| --- | --- | --- | --- |
| View warehouses and inventory | Yes | Yes | Yes |
| Create or edit warehouses | Yes | Yes | No |
| Delete an unused warehouse | Yes | Yes | No |
| Receive or adjust stock | Yes | Yes | No |

The API enforces these permissions independently of the permission-aware UI.

## Warehouse API

| Method | Path | Behavior |
| --- | --- | --- |
| `POST` | `/api/warehouses` | Create a warehouse with a unique normalized code |
| `GET` | `/api/warehouses` | Searchable, sortable, paginated list |
| `GET` | `/api/warehouses/{id}` | Warehouse details |
| `PUT` | `/api/warehouses/{id}` | Partial warehouse update |
| `DELETE` | `/api/warehouses/{id}` | Delete only when no inventory history exists |

Warehouse codes are trimmed and uppercased. Attempting to delete a warehouse referenced by inventory returns `WAREHOUSE_IN_USE`.

## Inventory API

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/api/inventory` | Filtered inventory list plus aggregate totals |
| `GET` | `/api/inventory/{product_id}` | Inventory for one product across warehouses |
| `GET` | `/api/inventory/warehouse/{warehouse_id}` | Inventory held at one warehouse |
| `POST` | `/api/inventory/receive` | Add a positive received quantity |
| `POST` | `/api/inventory/adjust` | Apply a signed, non-zero quantity with a required reason |

The list supports product/warehouse search, warehouse and low-stock filters, pagination, and allowlisted sorting. It returns on-hand, reserved, available, and low-stock aggregates for the selected filters.

## Invariants

- Each product/warehouse pair has at most one inventory row.
- `available_quantity = quantity_on_hand - quantity_reserved`; it is never persisted separately.
- Available quantity at or below the product reorder level is considered low stock.
- Receipts accept positive quantities only.
- Adjustments accept positive or negative quantities, reject zero, and require a reason.
- An adjustment cannot reduce on-hand stock below reserved stock.
- Inactive products cannot receive inventory changes.
- Every successful receipt or adjustment creates a non-zero stock movement in the same transaction.

Movement types needed by future workflows already exist in the enum, but transfers and movement-history queries belong to Milestone 5.
