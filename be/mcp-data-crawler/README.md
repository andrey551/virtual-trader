# 🔌 MCP Data Crawler (Dynamic & Structured)

Đây là một Model Context Protocol (MCP) server được viết bằng Python, sử dụng trình duyệt **Playwright** và các bộ thư viện tài chính để cào dữ liệu động, truy vấn tin tức vĩ mô, và lấy thông tin nến thị trường dưới dạng **cấu trúc JSON**. 

Server tích hợp sẵn cơ chế **Cache cục bộ (Thread-safe Cache)** và **Phân tích Tâm lý (Sentiment Analysis)** tự động.

---

## 🛠️ Các Thành Phần Core & Utilities

*   **Cache Manager (`src/utils/cache.py`)**: Cơ chế cache lưu trữ an toàn luồng (thread-safe) trong bộ nhớ với thời gian sống (TTL) tùy chỉnh (ví dụ: 15 giây cho giá trực tiếp, 30 phút cho nến lịch sử) để tránh bị chặn IP (Rate Limit) do yêu cầu trùng lặp.
*   **Sentiment Analyzer (`src/utils/sentiment.py`)**: Thuật toán phân tích sắc thái văn bản dựa trên từ khóa tài chính (Lexicon-based). Tính toán điểm Sentiment từ `-1.0` (cực kỳ tiêu cực/bearish) đến `+1.0` (cực kỳ tích cực/bullish).
*   **Playwright Crawler (`src/tools/crawler.py`)**: Trình thu thập dữ liệu web động bằng headless browser Chromium. Hỗ trợ chặn tải tài nguyên thừa (hình ảnh, fonts, stylesheet) để tăng tốc độ tải từ 3-5 lần, tự động cuộn (auto-scroll) kích hoạt AJAX, và cào dữ liệu bằng CSS Selectors.

---

## 🔧 Danh Sách 5 Công Cụ Tích Hợp (Registered Tools)

Server đăng ký 5 công cụ chuẩn MCP qua giao thức STDIO:

### 1. `get_market_price`
Lấy giá hiện tại, biên độ biến động tuyệt đối và phần trăm của một mã tài sản.
*   **Tham số đầu vào:**
    *   `ticker` (string, required): Mã tài sản (Ví dụ: `AAPL`, `TSLA`, `BTC-USD`, `EURUSD=X`, `^GSPC`).
*   **Luồng xử lý (3-Tier Fallback):** Thử lấy qua fast_info nhanh -> Parse Ticker JSON chi tiết -> Tính từ nến 5 ngày gần nhất.
*   **Kết quả:** JSON chứa `price`, `change`, `changePercent`, `currency` và `timestamp`.

### 2. `get_historical_candles`
Lấy dữ liệu nến lịch sử (OHLCV) hỗ trợ vẽ biểu đồ kỹ thuật.
*   **Tham số đầu vào:**
    *   `ticker` (string, required): Mã tài sản.
    *   `interval` (string, optional, enum): Độ dài nến (`1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo`). Mặc định: `1d`.
    *   `period` (string, optional, enum): Khoảng thời gian lấy (`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`). Mặc định: `1mo`.
*   **Kết quả:** Danh sách JSON chứa `time` (ISO date-time), `open`, `high`, `low`, `close`, `volume`.

### 3. `get_crypto_ticker`
Lấy dữ liệu giá và độ sâu sổ lệnh (Order Book Depth) trực tiếp từ API Binance.
*   **Tham số đầu vào:**
    *   `symbol` (string, required): Cặp giao dịch Binance (Ví dụ: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`).
    *   `depth` (integer, optional): Số bước giá bid/ask cần lấy (mặc định: `10`, tối đa `100`).
*   **Kết quả:** JSON chứa giá khớp gần nhất và danh sách các mức giá mua (`bids`)/bán (`asks`).

### 4. `get_market_news`
Quét tin tức kinh tế, tính toán điểm tâm lý và tự động gán mã tài sản bị ảnh hưởng.
*   **Tham số đầu vào:**
    *   `query` (string, required): Từ khóa tìm kiếm (Ví dụ: `OPEC`, `Federal Reserve`, `Bitcoin`).
    *   `limit` (integer, optional): Số lượng bài báo tối đa trả về (mặc định: `5`).
*   **Luồng xử lý:** Quét Google News RSS -> Bóc tách text qua BeautifulSoup -> Chạy thuật toán Sentiment -> Gán tag tài sản dựa trên từ khóa khớp (ví dụ: "oil spill" -> `USO`, `XOM`).
*   **Kết quả:** Danh sách tin tức kèm điểm sentiment (`sentiment_score`) và danh sách ticker liên đới (`tickers`).

### 5. `scrape_dynamic_page`
Cào nội dung văn bản hoặc dữ liệu theo CSS selectors từ URL bất kỳ.
*   **Tham số đầu vào:**
    *   `url` (string, required): Địa chỉ URL cần cào.
    *   `selectors` (object, optional): Bản đồ thuộc tính và CSS Selector tương ứng.
    *   `wait_selector` (string, optional): Selector chờ load trước khi cào.
    *   `raw_html` (boolean, optional): Nếu `True`, bỏ qua trình duyệt Chromium và cào tĩnh bằng requests nhanh.
*   **Kết quả:** JSON chứa tiêu đề trang và dữ liệu text/selectors bóc tách được.

---

## 🐳 Hướng dẫn Docker & Cài đặt

### 1. Khởi chạy độc lập (STDIO)
```bash
# Đứng tại be/mcp-data-crawler/
docker build -t mcp-data-crawler .
docker run -i --rm --ipc=host mcp-data-crawler
```
*Lưu ý: Flag `--ipc=host` ngăn lỗi tràn bộ nhớ dùng chung của trình duyệt Chromium.*

### 2. Tích hợp Claude Desktop
Thêm vào file cấu hình `%APPDATA%\Claude\claude_desktop_config.json`:
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
