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

Transfers, reservations, releases, shipments, and returns join this same flow in later milestones. Milestone 5 adds atomic two-warehouse transfers and the movement-history interface.

Receipts, adjustments, reservations, releases, shipments, transfers, and returns must create audit movements. Transfers update both locations and create both movements within one database transaction. Row-level locks will prevent concurrent reservations from overselling.
