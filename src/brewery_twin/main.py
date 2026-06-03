from fastapi import FastAPI

from brewery_twin.models import MeasurementIn
from brewery_twin import service #olokliro to module 

from fastapi import FastAPI, HTTPException

from pathlib import Path
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Brewery Digital Twin",
    description="A mini industrial digital twin for brewery process monitoring",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/measurements", status_code=201)
def create_measurement(measurement: MeasurementIn):
    new_id = service.record_measurement(measurement) #deixnw edw tin proeleusi
    return {
        "id": new_id,
        "message": "Measurement stored successfully",
    }
    
@app.get("/tanks/{tank_id}/stats")
def tank_stats(tank_id: int, sensor_type: str, minutes: int = 60):
    stats = service.get_tank_sensor_stats(tank_id, sensor_type, minutes)
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"No {sensor_type} data for tank {tank_id} in the last {minutes} minutes",
        )
    return stats

@app.get("/tanks/{tank_id}/anomalies")
def tank_anomalies(tank_id: int, sensor_type: str = "temperature", minutes: int = 30):
    result = service.get_tank_anomalies(tank_id, sensor_type, minutes)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active batch found for tank {tank_id}",
        )
    return result

@app.get("/tanks/{tank_id}/oee")
def tank_oee(tank_id: int, sensor_type: str = "temperature", minutes: int = 30):
    result = service.calculate_oee(tank_id, sensor_type, minutes)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active batch found for tank {tank_id}",
        )
    return result

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")