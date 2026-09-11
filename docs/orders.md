# Orders

Milestone 6 adds outbound orders and makes the backend the sole authority for every lifecycle transition and inventory effect.

## Access

| Operation | ADMIN | WAREHOUSE_MANAGER | EMPLOYEE |
| --- | --- | --- | --- |
| Create and view orders | Yes | Yes | Yes |
| Confirm, process, ship, complete | Yes | Yes | No |
| Cancel a pending order they created | Yes | Yes | Yes |
| Cancel any confirmed or processing order | Yes | Yes | No |

The UI hides unavailable actions, but the API independently enforces every permission and transition.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| `POST` | `/api/orders` | Create a pending order and snapshot current product prices |
| `GET` | `/api/orders` | Searchable, filterable, sortable, paginated order list |
| `GET` | `/api/orders/{id}` | Order header, creator, lines, and calculated total |
| `POST` | `/api/orders/{id}/confirm` | Reserve available stock |
| `POST` | `/api/orders/{id}/process` | Start fulfilment |
| `POST` | `/api/orders/{id}/ship` | Consume on-hand and reserved quantities |
| `POST` | `/api/orders/{id}/complete` | Close a shipped order |
| `POST` | `/api/orders/{id}/cancel` | Cancel and release reservations when present |

List filters include `search`, `order_status`, and `created_by`. Sorting is allowlisted to order number, status, created time, and updated time.

## Lifecycle and inventory rules

The forward path is `PENDING → CONFIRMED → PROCESSING → SHIPPED → COMPLETED`. Pending, confirmed, and processing orders may be cancelled. Completed, shipped, and already-cancelled orders are terminal for cancellation.

- Confirmation locks every affected inventory row in warehouse/product order, validates all lines, then increases reserved stock and records `RESERVE` movements.
- If any line is short, no line is reserved and the API returns `INSUFFICIENT_STOCK`.
- Cancellation of a confirmed or processing order decreases reserved stock and records `RELEASE` movements.
- Shipment decreases both on-hand and reserved stock and records `SHIPMENT` movements.
- Each movement uses `reference_type = ORDER` and the order ID as `reference_id`.
- The status, inventory balances, and movements commit or roll back in one PostgreSQL transaction.

See [order-flow.md](order-flow.md) for the state diagram.
