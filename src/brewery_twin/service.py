from brewery_twin.models import MeasurementIn
from brewery_twin import database #kanw import olo to module gia na exw prosbash stis synarthseis tou, den thelw na kanw import insert_measurement amesws giati isws tha thelw kai alles synarthseis argotera

def record_measurement(measurement: MeasurementIn) -> int:
    """Records a measurement in the database and returns the new record's ID."""
    new_id = database.insert_measurement(measurement)
    return new_id

def get_tank_sensor_stats(tank_id: int, sensor_type: str, minutes: int) -> dict | None:
    """
    Business logic gia ta stats: kalei tin database gia na parei ta raw aggregates, 
    meta kanw round ta apotelesmata gia na einai pio omorfa. 
    Epistrefei None an den yparxoun metrhseis stin parathiro.
    """
    raw = database.get_sensor_stats(tank_id, sensor_type, minutes)
    if raw is None:
        return None

    return {
        "tank_id": tank_id,
        "sensor_type": sensor_type,
        "window_minutes": minutes,
        "average": round(raw["avg_value"], 2),
        "minimum": round(raw["min_value"], 2),
        "maximum": round(raw["max_value"], 2),
        "readings": raw["readings"],
    }
    
def get_tank_anomalies(tank_id: int, sensor_type: str, minutes: int) -> dict | None:
    """Compute anomaly summary with a derived anomaly rate for presentation."""
    raw = database.get_anomaly_summary(tank_id, sensor_type, minutes)
    if raw is None:
        return None

    total = raw["total_readings"]
    anomalies = raw["anomalies"]
    rate = round(anomalies / total * 100, 1) if total > 0 else 0.0

    return {
        "tank_id": tank_id,
        "sensor_type": sensor_type,
        "window_minutes": minutes,
        "product_name": raw["product_name"],
        "limits": {"min": raw["temp_min"], "max": raw["temp_max"]},
        "total_readings": total,
        "anomalies": anomalies,
        "anomaly_rate_percent": rate,
    }
    
# Sensor sends one reading every 2 seconds → 30 readings per minute
EXPECTED_READINGS_PER_MINUTE = 30

# Placeholder: true Performance needs production-rate counters (ideal vs actual
# output), which our sensors don't provide. Documented assumption for the demo.
ASSUMED_PERFORMANCE = 0.95


def calculate_oee(tank_id: int, sensor_type: str, minutes: int) -> dict | None:
    
    # Xanaxrisimopoiw tin idia logiki anomaly (DRY) anti na tin ksanagrapsw edw:
    # an allaksei o orismos tou anomaly, ola ta KPIs menoun synepi.
    
    anomaly = get_tank_anomalies(tank_id, sensor_type, minutes)
    if anomaly is None:
        return None

    # Quality
    quality = 1.0 - (anomaly["anomaly_rate_percent"] / 100.0)

    # Availabilty: posa apo ta expected data ftasane ( capped sto 1.0 )
    actual = anomaly["total_readings"]
    expected = minutes * EXPECTED_READINGS_PER_MINUTE
    availability = min(actual / expected, 1.0) if expected > 0 else 0.0

    performance = ASSUMED_PERFORMANCE
    
    # Pollaplasiasmos kai OXI mesos oros: an enas paragontas einai 0
    # (px ola ta readings ektos oriwn -> quality=0) tote olo to OEE midenizei.
    # O mesos oros tha ekruve tin katastrofi.
    
    oee = availability * performance * quality

    return {
        "tank_id": tank_id,
        "sensor_type": sensor_type,
        "window_minutes": minutes,
        "product_name": anomaly["product_name"],
        "availability_percent": round(availability * 100, 1),
        "performance_percent": round(performance * 100, 1),
        "quality_percent": round(quality * 100, 1),
        "oee_percent": round(oee * 100, 1),
        "note": "Performance is an assumed placeholder; full OEE requires production-rate data.",
    }