# TechStar Shipment Analytics API

## Overview
This service tracks shipment records across carriers, letting the logistics dashboard create, retrieve, and analyze shipments by cost and status. It's used by the dashboard team to display real-time shipment data and summary metrics.

## Setup
```bash
pip install fastapi uvicorn
```
No environment variables are required — this version uses an in-memory data store (no database connection needed).

## Running Locally
```bash
cd day17/api
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

## Authentication
None required. This is an unauthenticated demo service — no tokens or API keys are needed to call any endpoint.

## Key Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | /shipments | List shipments, optionally filtered by carrier, with pagination |
| GET | /shipments/{shipment_id} | Retrieve a single shipment by ID |
| POST | /shipments | Create a new shipment (status defaults to "pending") |
| DELETE | /shipments/{shipment_id} | Delete a shipment by ID |
| GET | /analytics/summary | Get total shipment count, average freight cost, and status breakdown |

## Related Documentation
See `data-dictionary.md` in this folder for the full field-level schema of the `ShipmentResponse` model, and `ADR-001-postgresql-fleet-staging.md` for the database architecture decision from Day 10.