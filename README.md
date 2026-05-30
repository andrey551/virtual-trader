# Virtual Trader - Hệ Thống Phân Tích Thị Trường Tài Chính Toàn Cầu

Virtual Trader là một hệ thống phân tích và dự báo thị trường tài chính đa tài sản (chứng khoán quốc tế, tiền điện tử, ngoại hối, hàng hóa) dựa trên dữ liệu thời gian thực. Hệ thống sử dụng một mạng lưới đa tác nhân (Multi-Agent Swarm) được điều hành bởi mô hình **Gemini 1.5** và các công cụ thu thập dữ liệu bằng giao thức **Model Context Protocol (MCP)**.

Dự án này được thiết kế như một trợ lý phân tích đắc lực cho nhà đầu tư, không trực tiếp thực hiện giao dịch mà cung cấp các khuyến nghị kỹ thuật, phân tích vĩ mô, và lập bản đồ tác động của sự kiện địa chính trị thời gian thực thông qua một bảng điều khiển trực quan.

---

## 🏛️ Cấu Trúc Dự Án

Thư mục chính của dự án được phân tách rõ ràng thành Frontend và Backend:

```text
virtual-trader/
├── be/
│   └── mcp-data-crawler/    # Python MCP Server (Playwright, stdio)
│       ├── server.py        # Mã nguồn crawler và Yahoo Finance
│       ├── Dockerfile       # Đóng gói backend crawler
│       └── README.md        # Hướng dẫn chi tiết cho crawler
├── fe/
│   ├── src/                 # Next.js App Router (TypeScript)
│   ├── Dockerfile           # Đóng gói Multi-stage cho Next.js production
│   └── README.md            # Hướng dẫn chi tiết cho frontend
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI pipeline
├── .gitignore               # Cấu hình bỏ qua tệp tin Git (Loại trừ toàn bộ tệp .md ngoại trừ README.md)
└── README.md                # Tệp hướng dẫn chính này
```

---

## 🛠️ Công Nghệ Sử Dụng

*   **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS v4, TypeScript, Lucide Icons.
*   **Backend (MCP & Data Ingestion)**: Python 3.11, Playwright Async (Chromium headless), Python MCP SDK.
*   **AI Engine (Lộ trình dài hạn)**: Gemini 1.5 API, LangGraph / CrewAI.
*   **DevOps**: Docker, GitHub Actions CI Pipeline.

---

## 🚀 Hướng Dẫn Nhanh

### 1. Khởi Chạy Giao Diện (Frontend)
Đảm bảo bạn đã cài đặt Node.js 20+:
```bash
cd fe
npm install
npm run dev
```
Truy cập địa chỉ local tại [http://localhost:3000](http://localhost:3000).

### 2. Xây Dựng Backend Crawler (Docker)
Đảm bảo bạn đã khởi động Docker Desktop:
```bash
cd be/mcp-data-crawler
docker build -t mcp-data-crawler .
```

---

## 🔧 Tự Động Hóa CI Pipeline
Tệp workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) được cấu hình tự động chạy để kiểm tra và bảo đảm chất lượng code của cả Frontend và Backend, cũng như tính khả thi khi build Docker image trên môi trường đám mây của GitHub.
