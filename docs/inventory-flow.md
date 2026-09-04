# Inventory flow

Inventory workflows begin in Milestone 4. This document records the target behavior so implementation can be reviewed against it.

```mermaid
flowchart TD
    Request[Validated command] --> Lock[Lock inventory row]
    Lock --> Validate{Quantity valid?}
    Validate -->|No| Error[Rollback with standard error]
    Validate -->|Yes| Update[Update on-hand or reserved]
    Update --> Movement[Insert stock movement]
    Movement --> Commit[Commit transaction]
```

Receipts, adjustments, reservations, releases, shipments, transfers, and returns must create audit movements. Transfers update both locations and create both movements within one database transaction. Row-level locks will prevent concurrent reservations from overselling.

