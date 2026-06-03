from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from brewery_twin.config import DATABASE_URL
from brewery_twin.models import MeasurementIn

##anoigo kai kleinw argotera isws me pool 
@contextmanager
def get_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        
        


def insert_measurement(measurement: MeasurementIn) -> int:
    #apothikevei mia metrhsh kai epistrefei to id ths neas eggrafhs
    #Parameterized query (%s placeholders) gia na apofygoume SQL injection
    
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO measurements (tank_id, sensor_type, value, unit, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                measurement.tank_id,
                measurement.sensor_type.value,
                measurement.value,
                measurement.unit,
                measurement.timestamp,
            ),
        )
        new_row = cur.fetchone()
        return new_row["id"]
    
def get_sensor_stats(tank_id: int, sensor_type: str, minutes: int) -> dict | None:
    """
    Aggregate statistika gia ena sensor enos tank gia ta teleytaia N lepta. 
    Epistrefei None an den yparxoun metrhseis stin parathiro.
    """
    #parameterized query gia na apofygoume SQL injection
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT
                avg(value) AS avg_value,
                min(value) AS min_value,
                max(value) AS max_value,
                count(*)   AS readings
            FROM measurements
            WHERE tank_id = %s 
              AND sensor_type = %s
              AND timestamp >= now() - make_interval(mins => %s)
            """,
            (tank_id, sensor_type, minutes),
        )
        row = cur.fetchone()
        # If there are no readings, avg/min/max are NULL → treat as "no data"
        if row is None or row["readings"] == 0:
            return None
        return row
    
    
    # JOIN twn measurements me to ENERGO batch (ended_at IS NULL) gia na parw
    # ta oria tou. Anomaly = kathe timi ektos twn temp_min/temp_max tou batch.
def get_anomaly_summary(tank_id: int, sensor_type: str, minutes: int) -> dict | None:
    """
    Count readings outside the active batch's limits for one tank/sensor.
    Joins measurements with the tank's active batch to get the thresholds.
    Returns None if the tank has no active batch.
    """
    
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT
                count(*) AS total_readings,
                count(*) FILTER (
                    WHERE m.value < b.temp_min OR m.value > b.temp_max
                ) AS anomalies,
                b.product_name,
                b.temp_min,
                b.temp_max
            FROM measurements m
            JOIN batches b ON b.tank_id = m.tank_id AND b.ended_at IS NULL
            WHERE m.tank_id = %s
              AND m.sensor_type = %s
              AND m.timestamp >= now() - make_interval(mins => %s)
            GROUP BY b.product_name, b.temp_min, b.temp_max
            """,
            (tank_id, sensor_type, minutes),
        )
        return cur.fetchone()
    
def count_readings(tank_id: int, sensor_type: str, minutes: int) -> int:
    """Count how many readings a tank/sensor produced in the last N minutes."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT count(*) AS readings
            FROM measurements
            WHERE tank_id = %s
              AND sensor_type = %s
              AND timestamp >= now() - make_interval(mins => %s)
            """,
            (tank_id, sensor_type, minutes),
        )
        row = cur.fetchone()
        return row["readings"] if row else 0