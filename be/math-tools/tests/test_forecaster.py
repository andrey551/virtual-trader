import unittest
import pandas as pd
import numpy as np
import os
import sys

# Ensure math-tools and its src folder is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.short_term import simulate_gbm
from src.models.medium_term import simulate_ets
from src.models.long_term import simulate_regression
from src.forecaster import predict_forecast

class TestForecasters(unittest.TestCase):
    def setUp(self):
        self.current_price = 150.0
        # Create small test pandas DataFrame
        dates = pd.date_range(end="2026-06-09", periods=50, freq="1D")
        np.random.seed(42)
        close_prices = 150.0 + np.cumsum(np.random.normal(0, 1.0, 50))
        self.candles = pd.DataFrame({
            "Close": close_prices,
            "Volume": np.random.randint(1000, 50000, 50)
        }, index=dates)

    def test_gbm_positive_momentum(self):
        base, adv = simulate_gbm(
            self.current_price, self.candles, momentum_direction=1.0, risk_multiplier=1.0, steps=5
        )
        self.assertEqual(len(base), 5)
        self.assertEqual(len(adv), 5)
        # With positive momentum, advance line should drift higher than baseline
        self.assertTrue(adv[-1] > base[-1])

    def test_gbm_negative_momentum(self):
        base, adv = simulate_gbm(
            self.current_price, self.candles, momentum_direction=-1.0, risk_multiplier=1.0, steps=5
        )
        self.assertEqual(len(base), 5)
        self.assertEqual(len(adv), 5)
        # With negative momentum, advance line should drift lower than baseline
        self.assertTrue(adv[-1] < base[-1])

    def test_ets_length(self):
        base, adv = simulate_ets(
            self.current_price, self.candles, momentum_direction=1.0, risk_multiplier=1.0, steps=5
        )
        self.assertEqual(len(base), 5)
        self.assertEqual(len(adv), 5)

    def test_regression_length(self):
        base, adv = simulate_regression(
            self.current_price, self.candles, momentum_direction=1.0, risk_multiplier=1.0, steps=5
        )
        self.assertEqual(len(base), 5)
        self.assertEqual(len(adv), 5)

    def test_predict_forecast_wrapper(self):
        args = {
            "ticker": "AAPL",
            "current_price": 150.0,
            "verdict": "BUY",
            "confidence": 75.0,
            "momentum_direction": 1.0,
            "risk_multiplier": 1.0,
            "volatility_outlook": "HIGH"
        }
        res = predict_forecast(args)
        self.assertIn("predict_price_5s", res)
        self.assertIn("predict_price_5m", res)
        self.assertIn("predict_price_5h", res)
        self.assertIn("predict_price_5d", res)
        self.assertIn("baseline_trajectory", res)
        self.assertIn("advanced_trajectory", res)
        
        self.assertEqual(len(res["predict_price_5s"]), 5)
        self.assertEqual(len(res["predict_price_5d"]), 5)

if __name__ == "__main__":
    unittest.main()
