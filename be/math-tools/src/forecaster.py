import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from src.models.short_term import simulate_gbm
from src.models.medium_term import simulate_ets
from src.models.long_term import simulate_regression

def fetch_candles_safely(ticker: str, period: str, interval: str, current_price: float) -> pd.DataFrame:
    """
    Fetches historical candle data from the Backend Core candles API.
    If it fails or returns empty data (e.g. offline or API down),
    generates realistic mock historical candles starting from current_price.
    """
    # Resolve the Backend base URL:
    # If MCP_USE_DOCKER=True, we call the backend service container: http://backend:8000
    # Otherwise, we call localhost:8000
    use_docker = os.getenv("MCP_USE_DOCKER", "False").lower() in ("true", "1", "yes")
    backend_base = "http://backend:8000" if use_docker else "http://localhost:8000"
    
    url = f"{backend_base}/api/assets/{ticker}/candles"
    params = {"interval": interval, "period": period}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("candles"):
                candles_list = data["candles"]
                df = pd.DataFrame(candles_list)
                
                # Map JSON columns to DataFrame columns
                df = df.rename(columns={
                    "close": "Close",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "volume": "Volume",
                    "time": "Date"
                })
                
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                
                df["Close"] = df["Close"].astype(float)
                if "Volume" in df.columns:
                    df["Volume"] = df["Volume"].astype(float)
                
                if not df.empty and len(df) > 5:
                    return df
    except Exception as e:
        print(f"[Math Forecaster] Failed to fetch candles from Backend API ({url}): {e}. Using mock fallback.")

    # Generative mock fallback
    num_candles = 100
    if interval == "1m":
        freq = "min"
    elif interval == "1h":
        freq = "h"
    else:
        freq = "D"
        
    dates = pd.date_range(end=datetime.now(), periods=num_candles, freq=freq)
    
    np.random.seed(42)
    returns = np.random.normal(0.0001, 0.005, size=num_candles)
    price_series = current_price * np.exp(np.cumsum(returns) - returns.sum())
    
    df = pd.DataFrame({
        "Close": price_series,
        "Volume": np.random.randint(1000, 50000, size=num_candles)
    }, index=dates)
    
    return df

def predict_forecast(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestrator called by the MCP Server.
    Coordinates fetching historical candles and running forecast models.
    """
    ticker = args.get("ticker", "AAPL")
    current_price = float(args.get("current_price", 100.0))
    consensus_verdict = args.get("consensus_verdict", "HOLD")
    consensus_confidence = float(args.get("consensus_confidence", 50.0))
    momentum_direction = float(args.get("momentum_direction", 0.0))
    risk_multiplier = float(args.get("risk_multiplier", 1.0))
    volatility_outlook = args.get("volatility_outlook", "MEDIUM")

    # 1. Fetch candles for each horizon
    # 5s and 5m horizon needs 1-minute candles
    candles_1m = fetch_candles_safely(ticker, period="1d", interval="1m", current_price=current_price)
    
    # 5h horizon needs 1-hour candles
    candles_1h = fetch_candles_safely(ticker, period="1wk", interval="1h", current_price=current_price)
    
    # 5d horizon needs 1-day candles
    candles_1d = fetch_candles_safely(ticker, period="3mo", interval="1d", current_price=current_price)

    # 2. Run GBM for 5s and 5m
    _, p_5s_adv = simulate_gbm(
        current_price, candles_1m, momentum_direction, risk_multiplier, steps=5, interval_type="5s"
    )
    _, p_5m_adv = simulate_gbm(
        current_price, candles_1m, momentum_direction, risk_multiplier, steps=5, interval_type="5m"
    )

    # 3. Run ETS for 5h
    _, p_5h_adv = simulate_ets(
        current_price, candles_1h, momentum_direction, risk_multiplier, steps=5
    )

    # 4. Run Bayesian Ridge Regression for 5d
    p_5d_base, p_5d_adv = simulate_regression(
        current_price, candles_1d, momentum_direction, risk_multiplier, steps=5
    )

    return {
        "predict_price_5s": p_5s_adv,
        "predict_price_5m": p_5m_adv,
        "predict_price_5h": p_5h_adv,
        "predict_price_5d": p_5d_adv,
        "baseline_trajectory": p_5d_base,
        "advanced_trajectory": p_5d_adv
    }
