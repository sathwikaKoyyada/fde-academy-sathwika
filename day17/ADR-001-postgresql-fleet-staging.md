# ADR-001: PostgreSQL as Fleet Management Staging Database

## Status
Accepted

## Context
Day 10 required a relational staging layer to model fleet operations — vehicles, drivers, trips, mechanics, maintenance records, and a many-to-many driver-vehicle assignment relationship. The schema needed enforced foreign keys, junction table support, and compatibility with DBeaver for ERD verification. The environment already had PostgreSQL 15 running locally (fde_user/fde_academy) from Day 2 setup.

## Decision
Used PostgreSQL 15 as the staging database for the fleet management schema, with five core entity tables (vehicle, driver, trip, mechanic, maintenance) and a driver_vehicle_assignment junction table to model the many-to-many relationship.

## Alternatives Considered
- SQLite: rejected because it lacks native support for concurrent multi-user access and has weaker enforcement of foreign key constraints by default (must be manually enabled per connection), which was risky for a schema relying heavily on referential integrity across five linked tables.
- MySQL: rejected because the FDE Academy toolchain (DBeaver ERD tooling, later Foundry pipeline connections) was already standardized on PostgreSQL from Day 2 onward, and switching engines mid-program would break consistency with later exercises (Day 12 KPI aggregation also used the same fde_academy database).

## Consequences
+ Reusing the same PostgreSQL instance from Day 2 meant zero new environment setup — could go straight to schema design and ERD verification.
- The junction table approach for driver_vehicle_assignment adds query complexity (extra joins) for any report needing "current driver of vehicle X," compared to a simpler denormalized single-table design that would sacrifice historical assignment tracking.