# 🏛️ FastAPI Backend Core Orchestrator

This is the central brain (Orchestrator Core) of the **Virtual Trader** project, built using the **FastAPI** framework. The Backend Core communicates directly with the MCP Data Crawler via standard input/output (STDIO) to update asset data, schedules macroeconomic news scraping, records investment recommendations, and invokes the LangGraph Swarm Debate Engine to coordinate AI agent arguments.

---

## 🏗️ Components & Architecture

* **Database Config (`src/database.py`, `src/config.py`)**: Manages database sessions utilizing the **SQLAlchemy** ORM. Default configuration falls back to a local **SQLite** database (`sqlite:///./virtual_trader.db`) for rapid local development and testing, with support for **PostgreSQL** in production environments.
* **Relational Models (`src/models/`)**: Defines the relational schemas:
  * `asset.py`: Stores monitored assets (Ticker, Category, Consensus Verdict, Confidence Level, Hit Rate Accuracy).
  * `event.py`: Stores economic and geopolitical events, impact scores, and asset mappings (with pgvector embedding support for PostgreSQL).
  * `recommendation.py`: Stores generated trade entry zones, stop losses, profit targets, performance status, and returns.
  * `debate.py`: Stores conversation history and outputs of Swarm Agent debate sessions.
  * `prediction_cache.py`: Caches AI predictions to optimize Gemini API costs.
  * `knowledge_graph.py`: Defines nodes and edges of the multi-relation knowledge graph.
* **Stdio MCP Client (`src/services/mcp_client.py`)**: A thread-safe singleton manager that maintains the Playwright MCP crawler subprocess over standard I/O (STDIO), enabling API routers to call web tools directly.
* **Background News Worker (`src/workers/news_scheduler.py`)**: Leverages **APScheduler** to scan global financial RSS feeds (e.g. Google News) every 60 seconds. New articles are downloaded, analyzed for sentiment (Bullish/Bearish), and mapped to affected assets.

---

## 🔌 API Endpoints & WebSockets

### 1. REST API Router (`src/routes/`)

* **Assets Router (`/api/assets`)**:
  * `GET /api/assets`: Returns a list of all monitored tickers. Seeds default indices and assets (e.g., BTC-USD, AAPL, EURUSD=X) if the database is empty.
  * `GET /api/assets/{ticker}`: Returns details for a specific asset. If the ticker is unregistered, it initiates a price fetch via MCP and saves the asset.
  * `GET /api/assets/{ticker}/candles`: Fetches historical price candle bars from yFinance via the MCP crawler client based on user-defined `interval` and `period`.
* **Events Router (`/api/events`)**:
  * `GET /api/events`: Returns recent macroeconomic events, their market sentiment, and lists of affected asset tickers.
* **Recommendations Router (`/api/recommendations`)**:
  * `GET /api/recommendations`: Returns active and closed system-suggested trading signals.
* **MCP Bridge Router (`/api/mcp`)**:
  * `POST /api/mcp`: Provides an HTTP bridge allowing clients to invoke registered MCP tools directly.
* **Knowledge Graph Router (`/api/knowledge-graph`)**:
  * `GET /api/knowledge-graph/asset/{ticker}`: Returns nodes and edges within a 2-hop radius centered around the specified asset.
  * `POST /api/knowledge-graph/clean`: Manually triggers the edge weight decay loop (temporary weights decay by 5% toward baseline levels).
  * `POST /api/knowledge-graph/seed`: Pre-populates the database with initial sectors, indicators, and abstract nodes.

### 2. Real-Time WebSockets

* **Live Quote Feed `/ws/prices?tickers=BTC-USD,EURUSD=X`**: Subscribes to real-time price updates. To optimize network bandwidth, **updates are only pushed down to the client when the price changes by 0.15% or more** (`diff_pct >= 0.0015`).
* **Swarm Debate Stream `/ws/swarm-debate/{session_id}`**: Coordinates the LangGraph Swarm Engine. Upon client request, FastAPI spawns the independent CLI swarm engine (`be/swarm-engine/src/main.py`) as a subprocess, parsing stdout outputs and streaming them chunk-by-chunk down the WebSocket using a typewriter effect.

---

## 🚀 Setup & Execution (Local Development)

### 1. Prerequisites
* Python 3.11+
* Ensure Docker is running if configuring container integrations.

### 2. Install Dependencies
```bash
# From the be/backend-core directory
pip install -r requirements.txt
```

### 3. Run the Development Server
Start the FastAPI server via **Uvicorn**:
```bash
python -m uvicorn src.main:app --port 8000
```
* Swagger interactive documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).
* **Note**: Ensure the local `mcp-data-crawler` image is built or running if `MCP_USE_DOCKER` is configured, as the backend will initiate handshakes on startup.
