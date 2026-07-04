# 🎭 LangGraph Swarm Debate Engine

This is an **independent Swarm Agents module** responsible for conducting multi-dimensional debate sessions between specialized AI characters (AI Specialists) to analyze market dynamics and generate precise trading recommendations. The module utilizes **LangGraph** to build a StateGraph coordination flow, integrating vector-based queries for historical macroeconomic analogies (via pgvector or SQLite fallback).

---

## 🎨 State Graph & Debate Process (LangGraph Workflow)

```text
RetrieveAnalogy ──> Specialists Analysis ──> Peer Debate ──> Risk Management ──> Moderator Consensus
```

1. **RetrieveAnalogy**: Centers the analysis by querying PostgreSQL pgvector (or SQLite) for **3 similar historical events** and retrieves the subsequent 5-day price fluctuations of the asset. It also traverses the Multi-Relation Knowledge Graph within a 2-hop radius and calculates live technical indicators.
2. **Specialists Analysis (Round 1)**: Initiates independent analysis rounds. Specialized analysts join based on the asset category, returning structured opinions (Verdict, Confidence, Analysis, and Key Argument) utilizing Pydantic models.
3. **Peer Debate (Round 2)**: Conducts a cross-critique debate session. Active agents review Round 1 opinions and respond converse-style based on their distinct personalities.
4. **Risk Management**: The Risk Manager audits the debate, calculates optimal position sizing, and defines defensive entry ranges, target profit levels, and stop losses.
5. **Moderator Consensus**: The Swarm Moderator synthesizes the debate, weighs arguments, and determines the final consensus verdict and confidence. It then calls the `math-tools` MCP server to generate price trajectories, and runs a final validation check of the quantitative projections against the qualitative consensus and risk parameters.

---

## 🎭 10 Specialized AI Personas

Each agent is defined by a distinct system prompt and personality:
1. **Technical Analyst (`TECH_A`)**: Hyper-rational, chart-focused, and skeptical of hype. Relies on RSI, MACD, and volume profiles.
2. **Fundamental Analyst (`FUND_A`)**: Conservative value investor modeled after Warren Buffett. Focuses on earnings quality, margins, Moats, and cash flows.
3. **Macroeconomics Specialist (`MACRO_A`)**: Academic and systemic. Evaluates central bank interest policies, CPI, M2 supply, and yields.
4. **Geopolitical Analyst (`GEOPOL_A`)**: Alert and pragmatic. Views market changes as secondary to state embargoes, OPEC quotas, and resource conflicts.
5. **Sentiment Lead (`SENT_A`)**: Energetic and retail-focused. Monitors Twitter, Reddit, and fear-and-greed indexes to warn of crowd euphoria or FUD.
6. **Crypto Specialist (`CRYPTO_A`)**: Enthusiastic Web3 native. Analyzes smart contract logs, exchange inflows, whale wallet distributions, and gas fees.
7. **Forex Specialist (`FOREX_A`)**: Globalist currency analyst. Monitors yield spreads, balance of payments, and trade balances.
8. **Commodity Specialist (`COMM_A`)**: Pragmatic physical industrialist. Tracks refinery capacity, supply chains, shipping queues, and metal inventories.
9. **Risk Manager (`RISK_M`)**: Paranoid capital preservation auditor. Focuses on worst-case scenarios, position sizing, and stop loss margins.
10. **Swarm Moderator (`MOD_O`)**: Objective and diplomatic synthesis engine. Reconciles arguments, calculates consensus scores, and handles trajectory evaluation.

---

## 🔄 Dual Execution Modes: Mock & Real API

To support local testing and save API credits, the Swarm Engine includes a fallback mechanism:
* **Without `GEMINI_API_KEY`**: Automatically launches **Mock Debate Simulation (`src/mock_debate.py`)**. It generates randomized, typewriter-delayed transcripts that match agent personas (e.g. Technical Analyst discussing RSI support) and outputs JSON payloads formatted identically to real agents, ensuring frontend compatibility.
* **With `GEMINI_API_KEY`**: Executes the live LangGraph state graph. The 9 Specialists run on **Gemini 2.5 Flash Lite** (optimizing cost and response speed) while the Swarm Moderator runs on **Gemini 2.5 Flash** (for synthesis and logic).

---

## 📊 Token & Caching Optimization

* **Baseline Cost**: Approximately **~$0.0106** per complete 3-round debate session (9 Flash Lite Specialists + 1 Flash Moderator).
* **Context Caching**: By utilizing **Gemini Context Caching** for the static system prompts of the 10 characters, input tokens are compressed by 50%, reducing execution cost to **~$0.006** per session.

---

## 🚀 Execution Guide (CLI)

### 1. Install Dependencies
```bash
# Navigate to be/swarm-engine
pip install -r requirements.txt
```

### 2. Run the CLI Subprocess
To test the LangGraph debate engine directly from your terminal:
```bash
# For PowerShell:
$env:GEMINI_API_KEY="your_api_key"
python src/main.py --ticker BTC-USD --price 67250.45 --category CRYPTO

# For Bash:
export GEMINI_API_KEY="your_api_key"
python src/main.py --ticker BTC-USD --price 67250.45 --category CRYPTO
```
The graph will execute and stream debate logs chunk-by-chunk to `stdout` in JSON format.

### 3. Run Verification Tests
To run unit and integration tests for the debate engine:
```bash
python test_engine.py
```
