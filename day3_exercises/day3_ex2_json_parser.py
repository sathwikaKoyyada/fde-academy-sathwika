API_RESPONSE = {
    "meta": {"request_id": "REQ-2024-001", "total_records": 3, "page": 1},
    "shipments": [
        {  # SH-001
            "id": "SH-001",
            "reference": "PO-AFB-2024-441",
            "status": {
                "code": "IN_TRANSIT",
                "description": "Package in transit to destination hub",
                "updated_at": "2024-01-20T08:15:00Z",
            },
            "carrier": {
                "name": "DHL Express",
                "code": "DHL",
                "service_type": "EXPRESS",
                "contact": {"email": "ops@dhl.in", "phone": "+91-22-12345678"},
            },
            "route": {
                "origin": {"city": "Mumbai", "state": "MH", "pin": "400001"},
                "destination": {"city": "Delhi", "state": "DL", "pin": "110001"},
                "estimated_delivery": "2024-01-22",
                "distance_km": 1450,
            },
            "events": [
                {
                    "ts": "2024-01-18T10:00:00Z",
                    "location": "Mumbai Warehouse",
                    "type": "PICKUP",
                },
                {
                    "ts": "2024-01-19T06:30:00Z",
                    "location": "Nagpur Hub",
                    "type": "IN_TRANSIT",
                },
                {
                    "ts": "2024-01-20T08:15:00Z",
                    "location": "Delhi Hub",
                    "type": "ARRIVED",
                },
            ],
            "charges": {
                "base": 850.0,
                "fuel_surcharge": 127.5,
                "gst": 177.75,
                "total": 1155.25,
            },
            "delay_days": 0,
        },
        {  # SH-002
            "id": "SH-002",
            "reference": "PO-AFB-2024-442",
            "status": {
                "code": "DELAYED",
                "description": "Delayed due to customs clearance",
                "updated_at": "2024-01-20T07:00:00Z",
            },
            "carrier": {
                "name": "FedEx India",
                "code": "FEDEX",
                "service_type": "STANDARD",
                "contact": {"email": "support@fedex.in"},
            },
            "route": {
                "origin": {"city": "Chennai", "state": "TN", "pin": "600001"},
                "destination": {"city": "Bangalore", "state": "KA", "pin": "560001"},
                "estimated_delivery": "2024-01-21",
                "distance_km": 346,
            },
            "events": [
                {
                    "ts": "2024-01-18T14:00:00Z",
                    "location": "Chennai Port",
                    "type": "PICKUP",
                },
                {
                    "ts": "2024-01-20T07:00:00Z",
                    "location": "Customs Delhi",
                    "type": "HELD",
                },
            ],
            "charges": {
                "base": 320.0,
                "fuel_surcharge": 48.0,
                "gst": 66.24,
                "total": 434.24,
            },
            "delay_days": 3,
        },
        {  # SH-003
            "id": "SH-003",
            "reference": None,
            "status": {"code": "DELIVERED", "updated_at": "2024-01-19T16:00:00Z"},
            "carrier": {
                "name": "BlueDart",
                "code": "BLUEDART",
                "service_type": "ECONOMY",
            },
            "route": {
                "origin": {"city": "Pune"},
                "destination": {"city": "Hyderabad", "state": "TS", "pin": "500001"},
                "estimated_delivery": "2024-01-19",
                "distance_km": 559,
            },
            "events": [
                {
                    "ts": "2024-01-17T09:00:00Z",
                    "location": "Pune Depot",
                    "type": "PICKUP",
                },
                {
                    "ts": "2024-01-19T16:00:00Z",
                    "location": "Hyderabad Depot",
                    "type": "DELIVERED",
                },
            ],
            "charges": {"base": 180.0, "gst": 32.4, "total": 212.4},
            "delay_days": 0,
        },
    ],
}


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    print(status)


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    carrier = shipment.get("carrier", {})
    print(status)
    print(carrier)


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    carrier = shipment.get("carrier", {})
    route = shipment.get("route", {})
    origin = route.get("origin", {})
    destination = route.get("destination", {})
    print(status)
    print(carrier)
    print(origin)
    print(destination)


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    carrier = shipment.get("carrier", {})
    route = shipment.get("route", {})
    origin = route.get("origin", {})
    destination = route.get("destination", {})
    charges = shipment.get("charges", {})
    events = shipment.get("events", [])
    print(charges)
    print(events)


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    carrier = shipment.get("carrier", {})
    route = shipment.get("route", {})
    origin = route.get("origin", {})
    destination = route.get("destination", {})
    charges = shipment.get("charges", {})
    events = shipment.get("events", [])

    if events:
        latest_event_type = events[-1].get("type")
        latest_event_loc = events[-1].get("location")
    else:
        latest_event_type = None
        latest_event_loc = None

    print(latest_event_type)
    print(latest_event_loc)


def extract_shipment_record(shipment: dict) -> dict:
    status = shipment.get("status", {})
    carrier = shipment.get("carrier", {})
    route = shipment.get("route", {})
    origin = route.get("origin", {})
    destination = route.get("destination", {})
    charges = shipment.get("charges", {})
    events = shipment.get("events", [])

    if events:
        latest_event_type = events[-1].get("type")
        latest_event_loc = events[-1].get("location")
    else:
        latest_event_type = None
        latest_event_loc = None

    return {
        "shipment_id": shipment.get("id"),
        "reference": shipment.get("reference"),
        "status_code": status.get("code"),
        "status_desc": status.get("description"),
        "status_desc": status.get("description"),
        "carrier_name": carrier.get("name"),
        "carrier_code": carrier.get("code"),
        "service_type": carrier.get("service_type"),
        "carrier_email": carrier.get("contact", {}).get("email"),
        "origin_city": origin.get("city"),
        "origin_state": origin.get("state"),
        "dest_city": destination.get("city"),
        "dest_state": destination.get("state"),
        "est_delivery": route.get("estimated_delivery"),
        "distance_km": route.get("distance_km"),
        "event_count": len(events),
        "latest_event_type": latest_event_type,
        "latest_event_loc": latest_event_loc,
        "charge_base": charges.get("base"),
        "charge_gst": charges.get("gst"),
        "charge_total": charges.get("total"),
        "delay_days": shipment.get("delay_days", 0),
    }


def parse_api_response(response: dict) -> list[dict]:
    return [extract_shipment_record(s) for s in response.get("shipments", [])]


def compute_carrier_summary(records: list[dict]) -> list[dict]:
    groups = {}

    for record in records:
        code = record.get("carrier_code")
        if code not in groups:
            groups[code] = []
        groups[code].append(record)

    summary = []

    for code, group_records in groups.items():
        carrier_name = group_records[0].get("carrier_name")
        shipment_count = len(group_records)

        total_revenue = sum(
            r.get("charge_total")
            for r in group_records
            if r.get("charge_total") is not None
        )

        delayed_count = sum(1 for r in group_records if r.get("delay_days", 0) > 0)

        avg_delay_days = round(
            sum(r.get("delay_days", 0) for r in group_records) / shipment_count, 1
        )

        summary.append(
            {
                "carrier_code": code,
                "carrier_name": carrier_name,
                "shipment_count": shipment_count,
                "total_revenue": total_revenue,
                "delayed_count": delayed_count,
                "avg_delay_days": avg_delay_days,
            }
        )

    return summary
if __name__ == "__main__":
    records = parse_api_response(API_RESPONSE)

    print("=== SHIPMENT RECORDS ===")
    for record in records:
        print(record)

    print("\n=== CARRIER SUMMARY ===")
    summary = compute_carrier_summary(records)

    for item in summary:
        print(item)
