from brewery_twin import service


def test_oee_is_multiplicative_zero_quality(monkeypatch):
    """If quality is 0 (100% anomalies), OEE must be 0 regardless of other factors."""
    # Fake anomaly result: 100% anomaly rate → quality = 0
    fake = {
        "anomaly_rate_percent": 100.0,
        "total_readings": 900,   # high → availability would be high
        "product_name": "Test Lager",
    }
    monkeypatch.setattr(service, "get_tank_anomalies", lambda t, s, m: fake)

    result = service.calculate_oee(tank_id=1, sensor_type="temperature", minutes=30)

    assert result["quality_percent"] == 0.0
    assert result["oee_percent"] == 0.0   # zero factor zeroes the whole product


def test_oee_healthy_case(monkeypatch):
    """No anomalies + full data → OEE equals performance (the only sub-100 factor)."""
    fake = {
        "anomaly_rate_percent": 0.0,     # quality = 100%
        "total_readings": 900,           # 30 min * 30/min = 900 expected → availability = 100%
        "product_name": "Test Ale",
    }
    monkeypatch.setattr(service, "get_tank_anomalies", lambda t, s, m: fake)

    result = service.calculate_oee(tank_id=1, sensor_type="temperature", minutes=30)

    assert result["quality_percent"] == 100.0
    assert result["availability_percent"] == 100.0
    assert result["performance_percent"] == 95.0
    assert result["oee_percent"] == 95.0   # 1.0 * 0.95 * 1.0


def test_oee_returns_none_without_batch(monkeypatch):
    """If there is no active batch, OEE should be None (→ 404 at the API)."""
    monkeypatch.setattr(service, "get_tank_anomalies", lambda t, s, m: None)

    result = service.calculate_oee(tank_id=99, sensor_type="temperature", minutes=30)

    assert result is None