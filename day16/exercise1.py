from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date

app = FastAPI(title="TechStar Shipment Analytics API", version="1.0.0")

shipments_db = [
    {
        "id": 1,
        "carrier": "BlueDart",
        "ship_date": date(2026, 6, 1),
        "freight_cost": 450.0,
        "status": "delivered",
    },
    {
        "id": 2,
        "carrier": "Delhivery",
        "ship_date": date(2026, 6, 2),
        "freight_cost": 620.0,
        "status": "in_transit",
    },
    {
        "id": 3,
        "carrier": "BlueDart",
        "ship_date": date(2026, 6, 3),
        "freight_cost": 310.0,
        "status": "delivered",
    },
]
next_id = 4


class ShipmentCreate(BaseModel):
    carrier: str = Field(min_length=1)
    ship_date: date
    freight_cost: float = Field(gt=0)


class ShipmentResponse(BaseModel):
    id: int
    carrier: str
    ship_date: date
    freight_cost: float
    status: str


def get_pagination(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": min(limit, 50)}


@app.get("/shipments", response_model=list[ShipmentResponse])
def list_shipments(carrier: str | None = None, pagination=Depends(get_pagination)):
    results = shipments_db
    if carrier:
        results = [s for s in results if s["carrier"] == carrier]
    return results[pagination["skip"] : pagination["skip"] + pagination["limit"]]


@app.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: int):
    for s in shipments_db:
        if s["id"] == shipment_id:
            return s
    raise HTTPException(status_code=404, detail="Shipment not found")


@app.post("/shipments", response_model=ShipmentResponse, status_code=201)
def create_shipment(shipment: ShipmentCreate):
    global next_id
    new_shipment = {"id": next_id, "status": "pending", **shipment.model_dump()}
    shipments_db.append(new_shipment)
    next_id += 1
    return new_shipment


@app.get("/analytics/summary")
def analytics_summary():
    total = len(shipments_db)
    avg_cost = sum(s["freight_cost"] for s in shipments_db) / total if total else 0
    by_status = {}
    for s in shipments_db:
        by_status[s["status"]] = by_status.get(s["status"], 0) + 1
    return {
        "total_shipments": total,
        "average_freight_cost": round(avg_cost, 2),
        "by_status": by_status,
    }


@app.delete("/shipments/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int):
    for i, s in enumerate(shipments_db):
        if s["id"] == shipment_id:
            shipments_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Shipment not found")
