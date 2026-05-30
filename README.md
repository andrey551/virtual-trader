# 🌌 Virtual Trader - Hệ Thống Phân Tích Thị Trường Tài Chính Toàn Cầu

**Virtual Trader** là một hệ thống phân tích và dự báo thị trường tài chính đa tài sản (chứng khoán quốc tế, tiền điện tử, ngoại hối, chỉ số) thời gian thực. Hệ thống sử dụng một mạng lưới đa tác nhân (**Multi-Agent Swarm**) lập luận phản biện được điều hành bởi mô hình **Gemini 1.5** và các công cụ thu thập dữ liệu bằng giao thức **Model Context Protocol (MCP)**.

Dự án được thiết kế như một trợ lý phân tích đắc lực cho nhà đầu tư, không trực tiếp thực hiện giao dịch mà cung cấp các khuyến nghị kỹ thuật, phân tích vĩ mô, và lập bản đồ tác động của sự kiện địa chính trị thời gian thực thông qua một bảng điều khiển trực quan.

---

## 🏛️ Sơ Đồ Kiến Trúc Hệ Thống (Architecture Flow)

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

1.  **Giao Diện Người Dùng (fe/)**: Next.js Client hiển thị Watchlist, bản đồ tương quan sự kiện vĩ mô, và một **TradingView Lightweight Charts** terminal hỗ trợ xem nến lịch sử cùng nến dự báo của AI ở nhiều khung thời gian (`1m`, `5m`, `15m`, `1h`, `1d`).
2.  **Bộ Điều Phối (be/backend-core/)**: Máy chủ FastAPI xử lý REST API, quản lý cơ sở dữ liệu quan hệ (SQLite/PostgreSQL), duy trì bộ lập lịch background quét Google News vĩ mô, và duy trì các kết nối WebSocket trực tiếp.
3.  **MCP Data Crawler (be/mcp-data-crawler/)**: Server MCP Python giao tiếp qua STDIO. Sử dụng Playwright/Chromium để cào dữ liệu động, tích hợp yFinance truy vấn nến/giá, và tích hợp bộ phân tích sắc thái tin tức vĩ mô (Sentiment Analyzer).
4.  **Swarm Debate Engine (be/swarm-engine/)**: Động cơ tranh luận AI độc lập. Khi FastAPI gọi thực thi CLI qua tiến trình con (`asyncio.create_subprocess_exec`), Swarm Engine sẽ chạy đồ thị **LangGraph**:
    *   Truy vấn CSDL tìm **3 sự kiện tương đồng trong lịch sử** và lấy dữ liệu biến động giá làm cơ sở.
    *   Chạy 3 vòng phản biện chéo giữa 10 AI Agents có nhân cách riêng biệt.
    *   In kết quả dạng JSON line-by-line ra `stdout`. FastAPI hứng và chuyển tiếp ngay xuống Client qua WebSocket.

---

## 📂 Sơ Đồ Thư Mục Dự Án

```text
virtual-trader/
├── be/
│   ├── backend-core/        # FastAPI Core Orchestrator (Port 8000)
│   │   ├── src/models/      # SQLAlchemy Schemas (Asset, Event, Recommendation, Debate)
│   │   ├── src/routes/      # REST API & WebSockets (Prices, Swarm Debate)
│   │   └── virtual_trader.db# SQLite Database cục bộ
│   ├── mcp-data-crawler/    # Python Playwright MCP Server (STDIO)
│   │   ├── src/tools/       # Handlers cào web, yFinance, Binance API, Google News RSS
│   │   └── src/utils/       # Thread-safe Caching & Sentiment Scoring
│   └── swarm-engine/        # LangGraph AI Agents Debate Engine (CLI / Subprocess)
│       ├── src/personas.py  # System prompts định hình nhân cách cho 10 AI Agents
│       ├── src/graph.py     # Cấu trúc đồ thị LangGraph (Flash Specialists -> Pro Moderator)
│       └── src/mock_debate.py# Bộ mô phỏng offline typewriter debate khi thiếu API key
├── fe/                      # Next.js 16 Client Application (Port 3000)
│   ├── src/app/analysis/    # Analytics Terminal (Lightweight Charts v5 & Indicators)
│   ├── src/app/events/      # Bản đồ mạng lưới tương quan địa chính trị vĩ mô
│   └── src/components/      # Reusable Sidebar navigation và Layout
├── .github/workflows/       # GitHub Actions CI pipeline
└── README.md                # Tệp hướng dẫn tổng quan này
```

---

## 🛠️ Công Nghệ Sử Dụng

*   **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS v4, TypeScript, **TradingView Lightweight Charts v5**.
*   **FastAPI Backend**: FastAPI, SQLAlchemy, APScheduler (Background News Scanner), WebSockets.
*   **MCP Crawler**: Python, Model Context Protocol SDK, Playwright (Chromium headless), yFinance, BeautifulSoup.
*   **Swarm debate**: LangGraph, langchain-google-genai (**Gemini 1.5 Flash/Pro**), SQLite/pgvector.

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh (Local Quickstart)

Để khởi chạy toàn bộ hệ thống dưới local dev, bạn cần mở **3 cửa sổ Terminal** tương ứng với 3 service:

### Bước 1: Build Docker Image MCP Data Crawler
Đảm bảo bạn đã mở Docker Desktop, sau đó build image để FastAPI backend-core có thể gọi container:
```bash
cd be/mcp-data-crawler
docker build -t mcp-data-crawler .
```

### Bước 2: Khởi Chạy FastAPI Backend Core (Terminal 1)
Cài đặt thư viện Python và chạy máy chủ Uvicorn trên cổng `8000`:
```bash
cd be/backend-core
pip install -r requirements.txt
python -m uvicorn src.main:app --port 8000
```

### Bước 3: Khởi Chạy Next.js Frontend (Terminal 2)
Cài đặt thư viện Node và chạy máy chủ phát triển Next.js trên cổng `3000`:
```bash
cd fe
npm install
npm run dev
```

### Bước 4: Khởi Chạy Swarm Engine CLI độc lập (Tùy chọn - Terminal 3)
Nếu muốn chạy thử đồ thị tranh luận vĩ mô của 10 Agents trực tiếp dưới dòng lệnh:
```bash
cd be/swarm-engine
pip install -r requirements.txt
# Đảm bảo đã xuất biến môi trường nếu muốn dùng live Gemini API: export GEMINI_API_KEY="..."
python src/main.py --ticker BTC-USD --price 67250.45 --category CRYPTO
```

---

## 🔧 Tự Động Hóa CI Pipeline
Tệp workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) tự động kích hoạt trên GitHub để kiểm tra linter và build thử nghiệm Next.js/FastAPI/Docker, đảm bảo chất lượng tích hợp liên tục trước khi phát hành.
