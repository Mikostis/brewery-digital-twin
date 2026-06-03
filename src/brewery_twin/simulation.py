import random


def next_value(current: float, target: float, volatility: float, reversion: float) -> float:
    """Next sensor reading: random walk + mean reversion toward the target."""
    random_step = random.uniform(-volatility, volatility)
    pull_to_target = (target - current) * reversion
    return current + random_step + pull_to_target