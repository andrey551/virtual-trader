import numpy as np
import pandas as pd
from typing import List, Tuple

def simulate_gbm(
    current_price: float,
    candles: pd.DataFrame,
    momentum_direction: float,
    risk_multiplier: float,
    steps: int = 5,
    interval_type: str = "5s"
) -> Tuple[List[float], List[float]]:
    """
    Simulates Geometric Brownian Motion (GBM) for short-term asset price forecasting.
    Returns: (baseline_trajectory, advanced_trajectory)
    
    interval_type can be "5s" (1-second steps) or "5m" (1-minute steps).
    """
    if candles.empty or len(candles) < 2:
        # Fallbacks if historical data is insufficient
        baseline = [current_price] * steps
        advanced = [current_price] * steps
        return baseline, advanced

    # 1. Compute historical log returns
    # We assume candles has a 'Close' column
    close_prices = candles['Close'].astype(float).values
    log_returns = np.diff(np.log(close_prices))
    
    # Calculate historical drift and volatility per historical candle interval (typically 1m)
    mu_hist = np.mean(log_returns)
    sigma_hist = np.std(log_returns)
    if np.isnan(mu_hist) or mu_hist == 0:
        mu_hist = 0.0001
    if np.isnan(sigma_hist) or sigma_hist == 0:
        sigma_hist = 0.01

    # 2. Scale parameters to step size delta_t
    # If candles are 1-minute interval:
    # For "5s": delta_t = 1/60 (since steps are 1 second)
    # For "5m": delta_t = 1.0 (steps are 1 minute)
    if interval_type == "5s":
        delta_t = 1.0 / 60.0
    else:
        delta_t = 1.0

    # Scale drift and volatility
    mu_step = mu_hist * delta_t
    sigma_step = sigma_hist * np.sqrt(delta_t)

    # 3. Baseline Projection (pure mathematical expectation)
    # E[S_t] = S_0 * exp(mu * t)
    baseline_trajectory = []
    for step in range(1, steps + 1):
        p_base = current_price * np.exp(mu_step * step)
        baseline_trajectory.append(float(round(p_base, 4)))

    # 4. Swarm-Adjusted Projection (Advance Line)
    # Shift drift based on momentum_direction (-1.0 to 1.0)
    # Scale volatility based on risk_multiplier (0.5 to 2.0)
    # drift shift is scaled based on step size
    mu_adj = mu_step + (0.0005 * momentum_direction * delta_t)
    sigma_adj = sigma_step * risk_multiplier

    # We compute the expected value under the adjusted drift parameter
    # For the advance line, we also incorporate the volatility adjustment to simulate a slightly
    # biased trend expectation (often including risk premium or risk discount).
    # Expected value of GBM: E[S_t] = S_0 * exp(mu_adj * t)
    advanced_trajectory = []
    for step in range(1, steps + 1):
        p_adv = current_price * np.exp(mu_adj * step)
        advanced_trajectory.append(float(round(p_adv, 4)))

    return baseline_trajectory, advanced_trajectory
