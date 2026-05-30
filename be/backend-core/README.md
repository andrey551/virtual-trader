# 🏛️ FastAPI Backend Core

Đây là bộ não điều phối trung tâm (Orchestrator Core) của dự án **Virtual Trader**, được xây dựng bằng framework **FastAPI**. Backend Core kết nối trực tiếp với MCP Data Crawler thông qua giao thức STDIO để cập nhật dữ liệu tài sản, lên lịch quét tin tức vĩ mô, ghi nhận các gợi ý đầu tư, và kích hoạt Swarm Debate Engine chạy tranh luận AI.

---

## 🏗️ Kiến Trúc Các Thành Phần

*   **Database Config (`src/database.py`, `src/config.py`)**: Tích hợp ORM **SQLAlchemy** quản lý kết nối cơ sở dữ liệu. Mặc định tự động kết nối tới cơ sở dữ liệu cục bộ **SQLite** (`sqlite:///./virtual_trader.db`) giúp phát triển nhanh, và hỗ trợ cấu hình chuyển sang **PostgreSQL** trong môi trường Production.
*   **Relational Models (`src/models/`)**: Định nghĩa cấu trúc dữ liệu:
    *   `asset.py`: Lưu trữ các mã tài sản được theo dõi (Ticker, Category, Consensus Verdict, Confidence Level, Hit Rate Accuracy).
    *   `event.py`: Lưu trữ các sự kiện kinh tế/địa chính trị, điểm tác động, và bản đồ liên kết ảnh hưởng tài sản (hỗ trợ lưu trữ Vector Embedding cho PostgreSQL).
    *   `recommendation.py`: Lưu trữ gợi ý giao dịch (Entry, Target, Stop Loss, Returns, status).
    *   `debate.py`: Lưu trữ các phiên tranh luận của Swarm Agents.
*   **Stdio MCP Client (`src/services/mcp_client.py`)**: Singleton Client tự động khởi chạy và duy trì tiến trình con (subprocess) của MCP Data Crawler Server qua luồng STDIO chuẩn, cho phép gọi trực tiếp các tool cào dữ liệu và tin tức từ API FastAPI.
*   **Background Ingestion (`src/workers/news_scheduler.py`)**: Tích hợp bộ lập lịch **APScheduler** chạy vòng lặp ngầm định kỳ mỗi 60 giây. Worker này tự động gọi công cụ quét tin tức vĩ mô, bóc tách và phân loại sắc thái (Bullish/Bearish) rồi cập nhật cơ sở dữ liệu.

---

## 🔌 API Endpoints & WebSockets

### 1. REST API Router (`src/routes/`)
*   `GET /api/assets`: Trả về danh sách các mã tài sản đang được giám sát (Cổ phiếu, Crypto, Forex, Chỉ số). Tự động nạp hạt giống dữ liệu (seed data) nếu cơ sở dữ liệu trống.
*   `GET /api/assets/{ticker}`: Trả về thông tin chi tiết của một mã cụ thể. Nếu mã chưa được giám sát, tiến hành gọi mcp check giá và đưa vào cơ sở dữ liệu.
*   `GET /api/assets/{ticker}/candles`: Gọi mcp client lấy dữ liệu nến kỹ thuật theo `interval` (khung thời gian) và `period` (độ dài lịch sử) được truyền vào từ Client.
*   `GET /api/events`: Trả về các sự kiện macro ảnh hưởng đến thị trường kèm theo danh sách các tài sản bị ảnh hưởng tương ứng và điểm tác động.
*   `GET /api/recommendations`: Trả về lịch sử khuyến nghị giao dịch của hệ thống.
*   `POST /api/mcp`: Cổng HTTP Bridge cho phép gọi trực tiếp các công cụ của MCP từ bên ngoài.

### 2. Live WebSockets
*   **WebSocket Giá `/ws/prices?tickers=BTC-USD,EURUSD=X`**: Lắng nghe thay đổi giá trực tiếp. Để tiết kiệm băng thông, hệ thống **chỉ push dữ liệu xuống client khi giá có biến động mạnh (tỷ lệ thay đổi >= 0.15%)**.
*   **WebSocket Swarm Debate `/ws/swarm-debate/{session_id}`**: Lắng nghe luồng tranh luận. Khi nhận được tín hiệu kích hoạt từ Client, FastAPI sử dụng `asyncio.create_subprocess_exec` để gọi tiến trình con thực thi độc lập **Swarm Debate Engine** (`be/swarm-engine/src/main.py`), đọc luồng output `stdout` theo từng dòng và stream trực tiếp dạng typewriter xuống Frontend.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Yêu Cầu Hệ Thống
*   Python 3.11+
*   Dependencies cài đặt từ `requirements.txt`.

### 2. Cài Đặt Dependencies
```bash
# Đứng tại be/backend-core/
pip install -r requirements.txt
```

### 3. Chạy Môi Trường Phát Triển (Local Dev)
Khởi chạy máy chủ **Uvicorn**:
```bash
python -m uvicorn src.main:app --port 8000
```
Server sẽ chạy tại [http://localhost:8000](http://localhost:8000). Tài liệu API Swagger có thể xem tại [http://localhost:8000/docs](http://localhost:8000/docs).
*Lưu ý: Đảm bảo bạn đã build Docker image `mcp-data-crawler` trước khi chạy server, vì mcp client trong backend sẽ tự động spawn container mcp để giao tiếp.*
