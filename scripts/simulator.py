import random
import time
from datetime import datetime, timezone

import httpx

from brewery_twin.simulation import next_value

import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/measurements")
INTERVAL_SECONDS = 2.0

# Sensor definitions: which tank, sensor type, unit, target setpoint,
# volatility, reversion strength, and the running current value.
SENSORS = [
    {"tank_id": 1, "sensor_type": "temperature", "unit": "C",   "target": 18.0,  "volatility": 0.3,  "reversion": 0.1,  "value": 18.0},
    {"tank_id": 1, "sensor_type": "pressure",    "unit": "bar", "target": 1.2,   "volatility": 0.05, "reversion": 0.1,  "value": 1.2},
    {"tank_id": 2, "sensor_type": "temperature", "unit": "C",   "target": 20.0,  "volatility": 0.3,  "reversion": 0.1,  "value": 20.0},
    {"tank_id": 2, "sensor_type": "level",       "unit": "cm",  "target": 150.0, "volatility": 1.0,  "reversion": 0.05, "value": 150.0},
]


def next_value(current: float, target: float, volatility: float, reversion: float) -> float:
    """Next reading: random walk + mean reversion toward the target."""
    random_step = random.uniform(-volatility, volatility)
    pull_to_target = (target - current) * reversion
    return current + random_step + pull_to_target


def run() -> None:
    """Infinite loop: generate and POST a measurement for each sensor."""
    print(f"Simulator started. Sending to {API_URL} every {INTERVAL_SECONDS}s. Ctrl+C to stop.")
    with httpx.Client(timeout=5.0) as client:
        while True:
            for sensor in SENSORS:
                # Compute the new value based on the previous one
                sensor["value"] = next_value(
                    sensor["value"], sensor["target"], sensor["volatility"], sensor["reversion"]
                )

                payload = {
                    "tank_id": sensor["tank_id"],
                    "sensor_type": sensor["sensor_type"],
                    "value": round(sensor["value"], 2),
                    "unit": sensor["unit"],
                    # Always store UTC; convert to local only for display
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                try:
                    response = client.post(API_URL, json=payload)
                    if response.status_code == 201:
                        print(f"OK   tank {payload['tank_id']} {payload['sensor_type']:12} = {payload['value']}")
                    else:
                        print(f"WARN status {response.status_code}: {response.text}")
                except httpx.RequestError as exc:
                    # A gateway must not die on a dropped connection; log and continue
                    print(f"ERROR could not reach API: {exc}")

            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()