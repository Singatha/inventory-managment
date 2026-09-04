# Order flow

Order workflows begin in Milestone 6. The backend is the sole authority for state transitions.

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> CONFIRMED: reserve stock
    CONFIRMED --> PROCESSING
    PROCESSING --> SHIPPED: consume reservation
    SHIPPED --> COMPLETED
    PENDING --> CANCELLED
    CONFIRMED --> CANCELLED: release stock
    PROCESSING --> CANCELLED: release stock
```

Invalid transitions return a consistent conflict error. Confirmation locks affected inventory rows and reserves stock atomically. Cancellation releases reservations; shipment decreases both on-hand and reserved quantities.

