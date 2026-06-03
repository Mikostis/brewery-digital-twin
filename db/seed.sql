-- Seed tanks (physical, static)
INSERT INTO tanks (id, name, capacity_liters) VALUES
    (1, 'Fermentation Tank 1', 5000),
    (2, 'Fermentation Tank 2', 3000)
ON CONFLICT (id) DO NOTHING;

-- Seed one active batch per tank (ended_at = NULL means currently running)
INSERT INTO batches (tank_id, product_name, started_at, ended_at, temp_min, temp_max, pressure_min, pressure_max) VALUES
    (1, 'Pale Ale',  now() - interval '2 hours', NULL, 16.0, 20.0, 1.0, 1.5),
    (2, 'Pilsner',   now() - interval '1 hour',  NULL,  8.0, 14.0, 1.0, 1.4);