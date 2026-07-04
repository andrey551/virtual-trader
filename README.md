# 🌌 Virtual Trader - Global Financial Market Analysis System

**Virtual Trader** is a real-time, multi-asset financial market analysis and forecasting system (covering international equities, cryptocurrency, foreign exchange, indices, commodities, and derivatives). The system leverages a critical-reasoning network of multiple agents (**Multi-Agent Swarm**) orchestrated via **LangGraph** using **Gemini 2.5** models, with data acquisition powered by the **Model Context Protocol (MCP)**.

The system is designed as an analytical co-pilot for investors. It does not execute live trades directly. Instead, it provides technical recommendations, macroeconomic analysis, and correlation mapping of geopolitical events in real-time through an interactive dashboard interface.

---

## 🏛️ System Architecture Flow

```text
               +--------------------------------------+
               |        Next.js Frontend (fe/)        |
               +------------------+-------------------+
                                   ^
                     REST / WS    |   (JSON Live Stream)
                                   v
             +---------------------+-----------------------+
             |            FastAPI Backend Core             |
             |              (be/backend-core/)             |
             +----------+----------------------+-----------+
                        |                      |
             (STDIO)    |                      |   (Async Subprocess CLI)
                        v                      v
      +-----------------+--------+    +--------+-----------------+
      |   Playwright MCP Crawler |    |  LangGraph Swarm Engine  |
      |    (be/mcp-data-crawler/)|    |    (be/swarm-engine/)    |
      +--------------------------+    +--------+-----------------+
                                               |
                                               v  (SQL Query)
                                      +--------+-----------------+
                                      |    SQLite / PostgreSQL   |
                                      |   (similar past events)  |
                                      +--------------------------+
```

1. **User Interface (fe/)**: A Next.js client featuring a watchlist, geopolitical macro event correlation map, and a **TradingView Lightweight Charts v5** terminal. It displays historical candlesticks alongside AI-predicted candlesticks across multiple timeframes (`1m`, `5m`, `15m`, `1h`, `1d`).
2. **Orchestrator (be/backend-core/)**: A FastAPI server handling REST APIs, managing database structures (SQLite or PostgreSQL), maintaining background scheduler loops to scan global news, and managing live WebSockets connections.
3. **MCP Data Crawler (be/mcp-data-crawler/)**: A Python MCP server communicating via standard I/O (STDIO). It uses Playwright/Chromium to crawl dynamic websites, utilizes yFinance for market charts, and performs news sentiment scoring (Sentiment Analyzer).
4. **Swarm Debate Engine (be/swarm-engine/)**: An independent AI reasoning engine. When backend-core triggers the CLI via a subprocess (`asyncio.create_subprocess_exec`), the Swarm Engine runs a **LangGraph** state graph:
   * Queries the database to retrieve **3 similar historical events** and their subsequent 5-day price trajectories as empirical context.
   * Conducts up to 2 rounds of cross-criticism and debate among up to 10 AI Agents with highly distinct, customized personas.
   * Outputs JSON line-by-line to `stdout`, which FastAPI reads and streams to the client via WebSockets.

---

## 📂 Project Directory Structure

```text
virtual-trader/
├── be/
│   ├── backend-core/        # FastAPI Core Orchestrator (Port 8000)
│   │   ├── src/models/      # SQLAlchemy Schemas (Asset, Event, Recommendation, Debate)
│   │   ├── src/routes/      # REST API & WebSockets (Prices, Swarm Debate)
│   │   └── virtual_trader.db# Local SQLite Database
│   ├── mcp-data-crawler/    # Python Playwright MCP Server (STDIO)
│   │   ├── src/tools/       # Web scraping, yFinance, Binance API, Google News RSS tools
│   │   └── src/utils/       # Thread-safe Caching & Sentiment Scoring
│   ├── swarm-engine/        # LangGraph AI Agents Debate Engine (CLI / Subprocess)
│   │   ├── src/personas.py  # System prompts defining the 10 AI Agent personalities
│   │   ├── src/graph.py     # LangGraph state graph structure (Specialists -> Moderator)
│   │   └── src/mock_debate.py# Offline typewriter simulation fallback when API key is missing
│   └── math-tools/          # Math & ML forecasting MCP server (GBM, Holt-Winters, Bayesian Ridge)
├── fe/                      # Next.js 16 Client Application (Port 3000)
│   ├── src/app/analysis/    # Analytics Terminal (Lightweight Charts v5 & Indicators)
│   ├── src/app/events/      # Global macroeconomic & geopolitical correlation map
│   └── src/components/      # Reusable Sidebar navigation and layout components
├── .github/workflows/       # GitHub Actions CI pipeline
└── README.md                # General system overview guide
```

---

## 🛠️ Technology Stack

* **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS v4, TypeScript, **TradingView Lightweight Charts v5**.
* **FastAPI Backend**: FastAPI, SQLAlchemy, APScheduler (Background News Scanner), WebSockets.
* **MCP Crawler**: Python, Model Context Protocol SDK, Playwright (Chromium headless), yFinance, BeautifulSoup.
* **Swarm Debate**: LangGraph, langchain-google-genai (**Gemini 2.5 Flash/Flash-lite**), SQLite/pgvector.
* **Math Forecasting**: Python, NumPy, Pandas, scikit-learn (Bayesian Ridge), Statsmodels (Holt-Winters).

---

## 🚀 Local Quickstart Guide

To run the complete system locally, open **3 terminal windows** corresponding to each service:

### Step 1: Build the Playwright MCP Data Crawler Docker Image
Ensure Docker Desktop is running, then build the crawler image so backend-core can invoke it:
```bash
cd be/mcp-data-crawler
docker build -t mcp-data-crawler .
```

### Step 2: Start the FastAPI Backend Core (Terminal 1)
Install Python dependencies and run the Uvicorn development server on port `8000`:
```bash
cd be/backend-core
pip install -r requirements.txt
python -m uvicorn src.main:app --port 8000
```

### Step 3: Run the Next.js Frontend (Terminal 2)
Install node modules and start the development server on port `3000`:
```bash
cd fe
npm install
npm run dev
```

### Step 4: Run the Swarm Engine CLI (Optional - Terminal 3)
If you want to run the debate graph and output results directly to the command line:
```bash
cd be/swarm-engine
pip install -r requirements.txt
# Set environment variable: export GEMINI_API_KEY="..." (on Linux/macOS) or $env:GEMINI_API_KEY="..." (on PowerShell)
python src/main.py --ticker BTC-USD --price 67250.45 --category CRYPTO
```

---

## 🔧 Continuous Integration Pipeline
The workflow configuration file [.github/workflows/ci.yml](.github/workflows/ci.yml) triggers automatically on GitHub to verify linting and build tests for Next.js, FastAPI, and Docker configurations.

---

## 🧠 Multi-Relation Knowledge Graph

The system integrates a **Multi-Relation Knowledge Graph (Multigraph)** to represent financial structures (Assets, Sectors, Macroeconomic Indicators, Abstract Events) and trace the qualitative reasoning of AI agents:

1. **Semantic Graph Traversal**: When an asset is evaluated, the Swarm Engine traverses the graph within a 2-hop radius to gather complex relationships (e.g., `AAPL -> SUPPLIES -> Taiwan Semiconductor`, `Inflation -> INFLUENCES -> Interest Rates -> DEPRESSES -> Tech Sector`).
2. **Abstract Event Ingestion**: Scraped news articles are classified by AI into **Abstract Event Classes** (such as `Energy Supply Shock` or `Monetary Policy Action`). The link weights are updated dynamically using an **Exponential Moving Average (EMA)**.
3. **Cumulative Feedback Loop (Backpropagation)**: Once predictions are settled (marked as CLOSED), the system adjusts the weights of the traversed graph edges (e.g., if a bearish call was successful during an `Energy Supply Shock`, the connection `Energy Supply Shock -> DEPRESSES -> Sector` is strengthened).
4. **Automatic Settle/Decay**: Every 24 hours, temporary news-driven relationship weights decay by 5% to return to their historical baseline levels (`historical_base_weight`).
