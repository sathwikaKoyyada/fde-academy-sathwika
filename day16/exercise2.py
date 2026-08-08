from fastapi import BackgroundTasks
from exercise1 import app, shipments_db
import time
from datetime import datetime

refresh_status = {"state": "idle", "last_run": None}


def refresh_analytics():
    refresh_status["state"] = "running"
    time.sleep(5)
    _ = len(shipments_db)  # simulated recompute
    refresh_status["state"] = "complete"
    refresh_status["last_run"] = datetime.utcnow().isoformat()


@app.post("/analytics/refresh", status_code=202)
def trigger_refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_analytics)
    return {"message": "Refresh started"}


@app.get("/analytics/refresh-status")
def get_refresh_status():
    return refresh_status
