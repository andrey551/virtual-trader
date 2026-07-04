# 🔌 Playwright MCP Data Crawler

This is a Model Context Protocol (MCP) server written in Python that leverages the **Playwright** automation framework alongside financial libraries to crawl web pages, query economic indices, and acquire historical and real-time market telemetry as structured JSON payloads.

The server includes a thread-safe caching layer and a financial lexicon-based sentiment analysis engine.

---

## 🛠️ Core Utilities

* **Cache Manager (`src/utils/cache.py`)**: A thread-safe, in-memory cache with custom TTLs (e.g., 15 seconds for real-time tickers, 30 minutes for historical bars) to prevent IP blocks and rate limits from external APIs.
* **Sentiment Analyzer (`src/utils/sentiment.py`)**: A lexicon-based keyword matching algorithm tailored for financial headlines. It produces a sentiment score between `-1.0` (strongly bearish) and `+1.0` (strongly bullish).
* **Playwright Web Scraper (`src/tools/crawler.py`)**: A crawler powered by headless Chromium. It blocks non-essential assets (images, stylesheets, fonts) to increase performance, executes page auto-scrolls to trigger AJAX requests, and extracts data using CSS selectors.

---

## 🔧 Registered Tools

The server registers 5 primary tools over the STDIO channel:

### 1. `get_market_price`
Retrieves current spot prices, currency, daily changes, and percentage changes for global financial assets.
* **Input Parameters**:
  * `ticker` (string, required): Asset symbol (e.g. `AAPL`, `TSLA`, `BTC-USD`, `EURUSD=X`, `^GSPC`, `^VIX`).
* **Lookup Strategy**: Attempts a fast metadata lookup -> parses details from ticker tables -> falls back to calculating the average of the last 5 days of closing prices.
* **Returns**: JSON object containing `price`, `change`, `changePercent`, `currency`, and `timestamp`.

### 2. `get_historical_candles`
Retrieves historical OHLCV (Open, High, Low, Close, Volume) candlestick bars for technical charting.
* **Input Parameters**:
  * `ticker` (string, required): Asset symbol.
  * `interval` (string, optional, enum): Duration of each candle bar (`1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `1h`, `1d`, `5d`, `1wk`, `1mo`). Default is `1d`.
  * `period` (string, optional, enum): Extent of history to retrieve (`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`). Default is `1mo`.
* **Returns**: Array of candlestick bars containing `time` (ISO-8601), `open`, `high`, `low`, `close`, `volume`.

### 3. `get_crypto_ticker`
Queries spot exchange rates and order book depth directly from the Binance exchange API.
* **Input Parameters**:
  * `symbol` (string, required): Binance trading pair (e.g. `BTCUSDT`, `ETHUSDT`, `SOLUSDT`).
  * `depth` (integer, optional): Number of bid/ask levels to retrieve (default: `10`, maximum: `100`).
* **Returns**: JSON object containing `price` and lists of current `bids` and `asks`.

### 4. `get_market_news`
Scrapes macroeconomic RSS feeds, calculates article sentiment, and maps relevant asset tags.
* **Input Parameters**:
  * `query` (string, required): Headline search terms or tickers (e.g. `OPEC`, `Federal Reserve`, `NVIDIA`).
  * `limit` (integer, optional): Maximum articles to return (default: `5`).
* **Lookup Strategy**: Fetches feeds from Google News -> parses text content -> scores sentiment -> scans article keywords for known tickers (e.g. "interest rates" -> `EURUSD=X`, "oil spill" -> `USO`, `XOM`).
* **Returns**: Array of articles containing titles, urls, publication times, `sentiment_score`, and matching `tickers`.

### 5. `scrape_dynamic_page`
Crawls static HTML markup or renders dynamic javascript pages to extract text or selector-matched content.
* **Input Parameters**:
  * `url` (string, required): Target web page URL.
  * `selectors` (object, optional): Key-to-CSS-selector mappings (e.g., `{"title": "h1.entry-title", "price": ".price"}`).
  * `wait_selector` (string, optional): Selector to await before extracting.
  * `raw_html` (boolean, optional): If `True`, bypasses Chromium execution and executes a fast static HTML fetch.
* **Returns**: JSON object containing target page title and parsed text elements.

---

## 🐳 Dockerization & Configuration

### 1. Running the Container Independently (STDIO)
To run the server inside an isolated container:
```bash
# Build the image from be/mcp-data-crawler/
docker build -t mcp-data-crawler .

# Run the container
docker run -i --rm --ipc=host mcp-data-crawler
```
*Note: The `--ipc=host` flag is highly recommended to prevent headless Chromium from crashing due to shared memory limits.*

### 2. Integration with Claude Desktop Client
Add the following service configuration block to your `%APPDATA%\Claude\claude_desktop_config.json` file:
```json
{
  "mcpServers": {
    "mcp-data-crawler": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--ipc=host", "mcp-data-crawler"]
    }
  }
}
```
