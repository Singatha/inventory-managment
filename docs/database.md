# Database

PostgreSQL is the sole transactional datastore. SQLAlchemy 2.x uses its async API through `asyncpg`; Alembic owns all schema changes.

## Current schema

The initial revision is an intentionally empty baseline. Milestone 2 adds `users` and the PostgreSQL `user_role` enum. Milestone 3 adds `products`, including exact decimal prices, unique SKUs, non-negative checks, category/status indexes, and timestamps. Emails are normalized to lowercase before persistence and protected by a unique constraint. Password hashes are stored, never plaintext passwords.

## Planned relationships

```mermaid
erDiagram
    USER {
        bigint id PK
        varchar email UK
        varchar password_hash
        enum role
        boolean is_active
    }
    PRODUCT {
        bigint id PK
        varchar sku UK
        varchar name
        varchar category
        numeric price
        int reorder_level
        boolean is_active
    }
    PRODUCT ||--o{ INVENTORY : stocked_as
    WAREHOUSE ||--o{ INVENTORY : holds
    PRODUCT ||--o{ STOCK_MOVEMENT : records
    WAREHOUSE ||--o{ STOCK_MOVEMENT : records
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : ordered
    WAREHOUSE ||--o{ ORDER_ITEM : fulfilled_from
    SUPPLIER ||--o{ PURCHASE_ORDER : receives
    PURCHASE_ORDER ||--|{ PURCHASE_ORDER_ITEM : contains
```

The concrete schema and indexes will be documented alongside their migrations. Available quantity will be computed as `quantity_on_hand - quantity_reserved`, never stored.

## Migration policy

- Every schema change receives a reviewed Alembic revision.
- Production startup never calls ORM `create_all`.
- Downgrades should be safe when practical; destructive reversals require explicit operational review.
- Constraints protect invariants in addition to application validation.
