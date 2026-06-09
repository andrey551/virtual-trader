import numpy as np
import pandas as pd
from typing import List, Tuple
from sklearn.linear_model import BayesianRidge

def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators (RSI, MACD, SMA ratio, Volume surge) on a daily DataFrame.
    """
    df = df.copy()
    
    # 1. SMA Ratio (Close / 20-day SMA)
    df['sma_20'] = df['Close'].rolling(window=20).mean()
    df['sma_ratio'] = df['Close'] / df['sma_20']
    
    # 2. Volume Surge (Volume / 20-day average Volume)
    df['vol_sma_20'] = df['Volume'].rolling(window=20).mean()
    df['volume_surge'] = df['Volume'] / df['vol_sma_20']
    
    # 3. RSI (14-day)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 4. MACD Histogram
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    df['macd_hist'] = macd_line - signal_line
    
    # Fill NaNs
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    return df

def simulate_regression(
    current_price: float,
    candles: pd.DataFrame,
    momentum_direction: float,
    risk_multiplier: float,
    steps: int = 5
) -> Tuple[List[float], List[float]]:
    """
    Trains a Bayesian Ridge Regression model on daily technical indicators
    to forecast the next 5 days of asset prices.
    Returns: (baseline_trajectory, advanced_trajectory)
    """
    # Fallback if insufficient daily candles (require at least 25 candles to calculate 20 SMA & train)
    if candles.empty or len(candles) < 25:
        baseline = [current_price * (1 + 0.001 * i) for i in range(1, steps + 1)]
        advanced = [current_price * (1 + (0.001 + 0.005 * momentum_direction) * i) for i in range(1, steps + 1)]
        return baseline, advanced

    try:
        # 1. Calculate features
        df_feat = calculate_technical_features(candles)
        
        # 2. Build training dataset
        # Target: future log returns for 1 to 5 days
        # We will train 5 separate models, one for each horizon step (1d, 2d, 3d, 4d, 5d)
        feature_cols = ['sma_ratio', 'volume_surge', 'rsi', 'macd_hist']
        X = df_feat[feature_cols].values[:-steps]
        
        # Current feature vector to predict the future
        X_current = df_feat[feature_cols].values[-1].reshape(1, -1)
        
        baseline_trajectory = []
        std_errors = []
        
        for step in range(1, steps + 1):
            # Target is the price return 'step' days in the future
            y = np.log(df_feat['Close'].shift(-step) / df_feat['Close']).values[:-steps]
            
            # Clean NaNs in target (due to shift)
            valid_idx = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
            X_train = X[valid_idx]
            y_train = y[valid_idx]
            
            if len(X_train) < 10:
                raise ValueError("Insufficient clean training samples")
                
            model = BayesianRidge()
            model.fit(X_train, y_train)
            
            # Predict mean return and standard deviation
            pred_return, pred_std = model.predict(X_current, return_std=True)
            pred_price = current_price * np.exp(pred_return[0])
            baseline_trajectory.append(float(pred_price))
            std_errors.append(float(pred_std[0]))

    except Exception as e:
        # Robust fallback using standard trend line
        close_prices = candles['Close'].astype(float).values
        slope = (close_prices[-1] - close_prices[0]) / len(close_prices)
        baseline_trajectory = [float(current_price + slope * i) for i in range(1, steps + 1)]
        std_errors = [current_price * 0.01 * np.sqrt(i) for i in range(1, steps + 1)]

    # 3. Apply Swarm-Adjustment (advanced trajectory)
    # y_adj = y_base + (std_error * momentum_direction * risk_multiplier)
    # Convert standard errors (which are in log return space) to price adjustments
    advanced_trajectory = []
    for i, p_base in enumerate(baseline_trajectory):
        std_err = std_errors[i]
        # Shift in log space and exponentiate
        log_adj = std_err * momentum_direction * risk_multiplier * 1.5
        p_adv = p_base * np.exp(log_adj)
        advanced_trajectory.append(float(round(p_adv, 4)))

    # Format baseline
    baseline_trajectory = [float(round(p, 4)) for p in baseline_trajectory]

    return baseline_trajectory, advanced_trajectory
