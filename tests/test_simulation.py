from brewery_twin.simulation import next_value


def test_value_stays_close_to_current():
    """With zero volatility and zero reversion, value should not change."""
    result = next_value(current=18.0, target=18.0, volatility=0.0, reversion=0.0)
    assert result == 18.0


def test_reversion_pulls_toward_target():
    """With zero volatility, value moves toward the target (no randomness)."""
    # current below target → should move up
    result = next_value(current=10.0, target=20.0, volatility=0.0, reversion=0.5)
    assert result == 15.0  # 10 + (20-10)*0.5 = 15


def test_stays_within_volatility_bounds():
    """With zero reversion, the step is bounded by volatility."""
    current = 18.0
    volatility = 0.3
    for _ in range(1000):
        result = next_value(current, target=18.0, volatility=volatility, reversion=0.0)
        assert current - volatility <= result <= current + volatility