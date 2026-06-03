from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# Narrow/long: mia stili sensor_type + mia value. Neos aisthitiras = kamia
# allagi sto schema, mono nea timi sto enum. Vasiko gia epektasimotita.
class SensorType(str, Enum):
    temperature = "temperature"
    pressure = "pressure"
    level = "level"


class MeasurementIn(BaseModel):
    tank_id: int = Field(..., ge=1, description="Which tank this measurement belongs to")
    sensor_type: SensorType
    value: float
    unit: str = Field(..., min_length=1, max_length=10)
    timestamp: datetime