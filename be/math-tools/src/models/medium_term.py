import numpy as np
import pandas as pd
from typing import List, Tuple
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def simulate_ets(
    current_price: float,
    candles: pd.DataFrame,
    momentum_direction: float,
    risk_multiplier: float,
    steps: int = 5
) -> Tuple[List[float], List[float]]:
    """
    Fits an Exponential Smoothing (ETS) Holt-Winters model to medium-term historical candles.
    Returns: (baseline_trajectory, advanced_trajectory)
    """
    if candles.empty or len(candles) < 10:
        # Fallback if insufficient historical candles (e.g. less than 10 candles)
        baseline = [current_price * (1 + 0.0002 * i) for i in range(1, steps + 1)]
        advanced = [current_price * (1 + (0.0002 + 0.001 * momentum_direction) * i) for i in range(1, steps + 1)]
        return baseline, advanced

    # 1. Prepare candle series
    close_prices = candles['Close'].astype(float).values
    
    # 2. Fit Holt's Linear Trend Model (Double Exponential Smoothing)
    try:
        # We use simple additive trend
        model = ExponentialSmoothing(
            close_prices,
            trend='add',
            seasonal=None,
            initialization_method='estimated'
        )
        fitted_model = model.fit(optimized=True)
        
        # 3. Generate baseline forecast
        baseline_forecast = fitted_model.forecast(steps=steps)
        # Ensure it starts from current_price to avoid discontinuity
        offset = current_price - close_prices[-1]
        baseline_trajectory = [float(p + offset) for p in baseline_forecast]
    except Exception as e:
        # Fallback to linear trend if statsmodels fails
        slope = (close_prices[-1] - close_prices[0]) / len(close_prices)
        baseline_trajectory = [float(current_price + slope * i) for i in range(1, steps + 1)]

    # 4. Generate Swarm-Adjusted forecast (advanced trajectory)
    # Adjust trend component using momentum_direction (-1.0 to 1.0) and risk_multiplier
    # We add a drift shift relative to asset price volatility
    hist_vol = np.std(np.diff(close_prices))
    if np.isnan(hist_vol) or hist_vol == 0:
        hist_vol = current_price * 0.005

    advanced_trajectory = []
    for i, p_base in enumerate(baseline_trajectory):
        step = i + 1
        # Calculate adjustment: volatility * momentum * risk * step root-time scaling
        adj = hist_vol * momentum_direction * risk_multiplier * np.sqrt(step) * 0.2
        p_adv = p_base + adj
        advanced_trajectory.append(float(round(p_adv, 4)))

    # Ensure baseline outputs are formatted correctly
    baseline_trajectory = [float(round(p, 4)) for p in baseline_trajectory]

    return baseline_trajectory, advanced_trajectory
