-- Enable the TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Physical tanks:  static attributes
CREATE TABLE IF NOT EXISTS tanks (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    capacity_liters INTEGER NOT NULL
);

-- Production batches: time-bound, product-specific limits 
CREATE TABLE IF NOT EXISTS batches (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tank_id      INTEGER NOT NULL REFERENCES tanks(id),
    product_name TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL,
    ended_at     TIMESTAMPTZ,
    temp_min     DOUBLE PRECISION,
    temp_max     DOUBLE PRECISION,
    pressure_min DOUBLE PRECISION,
    pressure_max DOUBLE PRECISION
);

-- Raw data metrtisima : monadiki pigi alitheias
CREATE TABLE IF NOT EXISTS measurements (
    id          BIGINT       GENERATED ALWAYS AS IDENTITY,
    tank_id     INTEGER      NOT NULL,
    sensor_type TEXT         NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    unit        TEXT         NOT NULL,
    timestamp   TIMESTAMPTZ  NOT NULL,
    -- To timestamp einai meros tou PK giati i TimescaleDB xwrizei ta dedomena
    -- se chunks me vasi ton xrono.
    PRIMARY KEY (id, timestamp)
);

-- metatropi tou pinaka measurements se hypertable me vasi ton xrono (timestamp)
SELECT create_hypertable('measurements', 'timestamp', if_not_exists => TRUE);