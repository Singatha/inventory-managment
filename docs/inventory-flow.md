# Inventory flow

Milestone 4 implements receipts and reasoned adjustments through this transaction flow:

```mermaid
flowchart TD
    Request[Validated command] --> Lock[Lock inventory row]
    Lock --> Validate{Quantity valid?}
    Validate -->|No| Error[Rollback with standard error]
    Validate -->|Yes| Update[Update on-hand or reserved]
    Update --> Movement[Insert stock movement]
    Movement --> Commit[Commit transaction]
```

The service locks an existing `(product, warehouse)` balance with `SELECT ... FOR UPDATE`. The database additionally enforces non-negative on-hand and reserved quantities and ensures reserved quantity never exceeds on-hand quantity. A receipt or adjustment and its `StockMovement` audit row commit together or roll back together.

Milestone 5 extends the flow to two-sided transfers:

```mermaid
flowchart LR
    Validate[Validate product, warehouses, quantity] --> Lock[Lock inventory rows by warehouse ID]
    Lock --> Check{Enough available source stock?}
    Check -->|No| Rollback[Return conflict; persist nothing]
    Check -->|Yes| Balances[Decrease source and increase destination]
    Balances --> Pair[Create linked TRANSFER_OUT and TRANSFER_IN]
    Pair --> Commit[Commit one transaction]
```

Reservations, releases, shipments, and returns join this same flow with the order lifecycle in Milestone 6.

Receipts, adjustments, reservations, releases, shipments, transfers, and returns must create audit movements. Transfers update both locations and create both movements within one database transaction. Row-level locks will prevent concurrent reservations from overselling.
