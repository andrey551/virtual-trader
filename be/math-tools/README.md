# Math & ML Forecasting Service (`be/math-tools`)

A standalone mathematical and machine learning forecasting service for the Virtual Trader platform. 

This service is exposed as a **Model Context Protocol (MCP)** server communicating over standard input/output (`stdio`), separating the qualitative LLM-based agent reasoning inside the **Swarm Engine** from deterministic statistical/ML projections.

---

## 1. Core Architecture

The service runs independently inside the stack:
*   **Decoupled Payloads:** The Swarm Engine passes *only* the qualitative consensus variables (verdict, confidence, momentum, risk multiplier, and volatility outlook). It does not pass raw price histories.
*   **API-Driven Data Fetching:** Historical candle data is fetched dynamically from the **Backend Core Candles API** (`http://backend:8000/api/assets/{ticker}/candles` inside Docker) instead of scraping external web endpoints directly.
*   **Fallback Resilience:** If the Backend API is offline or unreachable, the forecaster falls back to a local high-fidelity mock random-walk candle generator to ensure the pipeline never crashes.

---

## 2. Forecast Models By Horizon

The service exposes projections over 4 distinct time horizons:

### 1. Short-Term (`5s` & `5m`): Geometric Brownian Motion (GBM)
For rapid, noisy horizons, prices are modeled as a stochastic process:
$$dS_t = \mu S_t dt + \sigma S_t dW_t$$
*   **Baseline:** Extrapolates standard drift ($\mu_{hist}$) and volatility ($\sigma_{hist}$) calculated from 1-minute historical candles.
*   **Swarm-Adjusted:** Modifies drift using $\mu_{adj} = \mu_{hist} + 0.0005 \times \text{momentum\_direction}$ and scales volatility using $\sigma_{adj} = \sigma_{hist} \times \text{risk\_multiplier}$.

### 2. Medium-Term (`5h`): Holt-Winters Exponential Smoothing (ETS)
Double Exponential Smoothing (Holt linear trend model) is fitted to 1-hour candles to capture hourly trends:
*   **Baseline:** Forecasts a linear historical trend.
*   **Swarm-Adjusted:** Modifies the trend slope based on the `momentum_direction` and multiplies the standard forecast deviation bounds by the `risk_multiplier`.

### 3. Long-Term (`5d`): Bayesian Ridge Regression
Trains 5 independent Bayesian Ridge models on daily technical indicators (`RSI`, `MACD Histogram`, `50 SMA Ratio`, `Volume Surge`) to forecast daily closing log returns:
*   **Baseline:** Projections fitted purely on historical coefficients.
*   **Swarm-Adjusted:** Pushes the prediction mean towards risk targets using standard error margins:
    $$\hat{y}_{adj} = \hat{y}_{base} + (\text{Standard\_Error} \times \text{momentum\_direction} \times \text{risk\_multiplier} \times 1.5)$$

---

## 3. Data Contracts

For precise details on JSON input parameters, exact range values (`[-1.0, 1.0]` for momentum, `[0.5, 2.0]` for risk multiplier), and outputs formats, refer directly to [contract.md](file:///c:/Users/Never/virtual-trader/be/math-tools/contract.md).

---

## 4. Local Installation & Development

To setup and run the service locally:

### Install Dependencies
```bash
# From repository root
pip install -r be/math-tools/requirements.txt
```

### Run Unit Tests
Verify model calculations and range behaviors:
```bash
# From repository root
python -m unittest be/math-tools/tests/test_forecaster.py
```

### Run MCP Server Locally (Manual Test)
You can spawn the server and send JSON-RPC protocol requests directly over standard input:
```bash
python be/math-tools/server.py
```

---

## 5. Docker Deployment

The service is packaged using its own isolated Dockerfile. It does not bloat the `backend-core` image.

### Build the Image Separately
```bash
docker build -t mcp-math-tools ./be/math-tools
```

### Build via Docker Compose
The image is integrated into `docker-compose.yml` under a `build-only` profile:
```bash
# Rebuild the MCP server container
docker compose build mcp-math-tools
```

In production, the **Swarm Engine** container triggers this service dynamically via the host's Docker socket:
```bash
docker run -i --rm mcp-math-tools
```
This routes standard input/output streams directly between the containers with zero networking overhead.
