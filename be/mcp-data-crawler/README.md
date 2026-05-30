# MCP Data Crawler (Dynamic & Structured)

Đây là một Model Context Protocol (MCP) server được viết bằng Python, sử dụng trình duyệt ẩn danh **Playwright** để cào dữ liệu động từ các trang web (bao gồm cả các trang SPA/Render bằng Javascript) và trả về dữ liệu **cấu trúc JSON**. Dữ liệu này được thiết kế để dễ dàng chuyển tiếp sang các component phân tích khác (như LLMs, trading bots, hoặc các script phân tích dữ liệu như Pandas).

Server được đóng gói bằng Docker sử dụng base image chính thức của Playwright Python nhằm đảm bảo tính đồng bộ và hoạt động ổn định trên mọi môi trường.

---

## 🛠️ Các Tool Cung Cấp

Server cung cấp 2 công cụ chính trả về kết quả định dạng JSON:

### 1. `get_market_price`
Lấy dữ liệu giá hiện tại và biến động thị trường của một mã chứng khoán/crypto từ Yahoo Finance.

*   **Tham số đầu vào:**
    *   `ticker` (string, required): Mã trading (Ví dụ: `AAPL`, `TSLA`, `BTC-USD`).
*   **Định dạng kết quả trả về (JSON string):**
    ```json
    {
      "status": "success",
      "ticker": "AAPL",
      "price": "180.25",
      "change": "-1.25 (-0.69%)",
      "timestamp": "2026-05-30T05:00:00.000000Z"
    }
    ```

### 2. `scrape_dynamic_page`
Cào dữ liệu động từ một trang web bất kỳ bằng CSS Selectors.

*   **Tham số đầu vào:**
    *   `url` (string, required): Địa chỉ URL cần cào.
    *   `selectors` (object, optional): Một object map tên thuộc tính mong muốn với CSS Selector tương ứng. Ví dụ: `{"title": "h1.header", "price": ".price-tag"}`.
    *   `wait_selector` (string, optional): CSS Selector cần đợi load trước khi bắt đầu lấy dữ liệu (hữu ích cho các trang web load chậm hoặc render bằng JS).
    *   `timeout` (integer, optional): Thời gian tối đa chờ trang web phản hồi (mặc định là `30000` ms).
*   **Định dạng kết quả trả về (JSON string):**
    *   *Trường hợp dùng selectors:*
        ```json
        {
          "status": "success",
          "url": "https://example.com/product",
          "data": {
            "_page_title": "Tên sản phẩm mẫu",
            "title": "Sản phẩm A",
            "price": "150,000 VND"
          },
          "timestamp": "2026-05-30T05:01:00.000000Z"
        }
        ```
    *   *Trường hợp không dùng selectors (mặc định lấy toàn bộ body text):*
        ```json
        {
          "status": "success",
          "url": "https://example.com/product",
          "data": {
            "_page_title": "Tên sản phẩm mẫu",
            "body_text": "Toàn bộ văn bản hiển thị trên trang..."
          },
          "timestamp": "2026-05-30T05:01:00.000000Z"
        }
        ```

---

## 🐳 Hướng dẫn với Docker

### 1. Build Docker Image
Đứng tại thư mục chứa file `Dockerfile` (`be/mcp-data-crawler/`), chạy lệnh sau để build image:
```bash
docker build -t mcp-data-crawler .
```

### 2. Chạy container ở chế độ thủ công (STDIO)
MCP Server giao tiếp qua Standard Input/Output (STDIO). Để chạy và tương tác trực tiếp với container:
```bash
docker run -i --rm --ipc=host mcp-data-crawler
```
*Lưu ý: Flag `--ipc=host` rất quan trọng khi sử dụng Playwright/Chromium để tránh lỗi hết bộ nhớ dùng chung (out of memory).*

---

## 🔌 Cấu hình tích hợp với Client (Ví dụ: Claude Desktop)

Để tích hợp server này vào ứng dụng Claude Desktop của bạn, hãy cập nhật file cấu hình MCP của bạn (`claude_desktop_config.json`):

*   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
*   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Thêm cấu hình chạy container Docker:

```json
{
  "mcpServers": {
    "mcp-data-crawler": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--ipc=host",
        "mcp-data-crawler"
      ]
    }
  }
}
```

Khởi động lại Claude Desktop là bạn đã có thể yêu cầu Claude sử dụng các tool cào dữ liệu và phân tích dữ liệu trực tiếp dưới định dạng JSON!
