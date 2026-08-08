DATA DICTIONARY: ShipmentResponse
SOURCE: GET /shipments, GET /shipments/{shipment_id}, POST /shipments
OWNER: Sathwika Koyyada
LAST UPDATED: 2026-08-08

| Field        | Type   | Nullable | Description                          | Example       |
|--------------|--------|----------|---------------------------------------|---------------|
| id           | int    | No       | Unique shipment identifier            | 1             |
| carrier      | string | No       | Name of the shipping carrier          | BlueDart      |
| ship_date    | date   | No       | Date the shipment was sent            | 2026-06-01    |
| freight_cost | float  | No       | Cost of shipping, must be > 0         | 450.0         |
| status       | string | No       | Current shipment state                | delivered     |

KNOWN LIMITATIONS: freight_cost has no upper bound validation, and status is a free-form string (not an enum), so typos in status values are possible when set internally (e.g. in create_shipment defaulting to "pending").