# 🎭 LangGraph Swarm Debate Engine

Đây là module **Swarm Agents độc lập** chịu trách nhiệm chạy các phiên thảo luận chuyên sâu đa chiều giữa các tác nhân trí tuệ nhân tạo (AI Specialists) để phân tích tác động thị trường và đưa ra các khuyến nghị giao dịch chuẩn xác. Module sử dụng **LangGraph** để xây dựng đồ thị trạng thái (StateGraph) phối hợp và tích hợp công cụ truy vấn độ tương đồng sự kiện vĩ mô quá khứ (**pgvector/SQLite Keyword Similarity**).

---

## 🎨 Đồ Thị Trạng Thái & Quy Trình Tranh Luận (LangGraph Workflow)

```text
RetrieveAnalogy ──> Specialists Analysis ──> Peer Debate ──> Risk Management ──> Moderator Consensus
```

1.  **RetrieveAnalogy**: Node đầu tiên truy cập Vector Database hoặc SQL Text Search để tìm ra **3 sự kiện tương đồng lớn nhất trong lịch sử** và lấy dữ liệu biến động giá sau 5 ngày của tài sản đó, làm cơ sở phân tích dữ liệu cho các tác nhân AI.
2.  **Specialists Analysis**: 9 chuyên gia độc lập thực hiện phân tích dựa trên kiến thức chuyên môn, đưa ra nhận định riêng và chấm điểm Consensus (BUY/SELL/HOLD) kèm mức độ tin cậy.
3.  **Peer Debate**: Chạy vòng phản biện chéo. Các chuyên gia đọc báo cáo của nhau và phản hồi đối chất dựa trên tính cách của từng nhân vật.
4.  **Risk Management**: Chuyên gia quản trị rủi ro bảo thủ tính toán quy mô vị thế lệnh tối đa và khuyến nghị điểm dừng lỗ (Stop Loss) an toàn để bảo vệ vốn.
5.  **Moderator Consensus**: Điều phối viên (Gemini 1.5 Pro) đúc kết nội dung, chấm điểm độ chính xác dự báo lịch sử, đưa ra Verdict cuối cùng kèm phân tích tổng hợp.

---

## 🎭 10 Nhân Cách AI Agents (Personas Prompting)

Mỗi Agent có một System Prompt và tính cách được cá nhân hóa sâu sắc:
1.  **Technical Analyst (Thực dụng & Nghi ngờ)**: Chỉ tin vào RSI, MACD, Volume.
2.  **Fundamental Specialist (Nhà đầu tư giá trị cổ điển)**: Modeled theo Warren Buffett. Tập trung dòng tiền, giá trị nội tại, ghét đầu cơ.
3.  **Macroeconomics Specialist (Hàn lâm)**: Quan tâm chu kỳ Fed, DXY, CPI, Yields.
4.  **Geopolitical Analyst (Cảnh giác)**: Nhìn mọi thứ qua OPEC, cấm vận, địa chính trị.
5.  **Sentiment Lead (Nhạy bén MXH)**: Phân tích FUD, FOMO, Whales trên Twitter/Reddit.
6.  **Crypto Specialist (Web3 Native)**: Chuyên gia on-chain phân tích dòng tiền ví cá voi, pools.
7.  **Forex Specialist (Toàn cầu)**: Tập trung chênh lệch lãi suất, tỷ giá fiat chéo.
8.  **Commodity Specialist (Công nghiệp)**: Theo dõi công suất dầu khí, chuỗi cung ứng vật lý.
9.  **Risk Manager (Bảo thủ & Hoang tưởng)**: Luôn giả định thị trường sập để tính Stop Loss.
10. **Swarm Moderator (Ngoại giao & Khách quan)**: Tổng hợp, hòa giải ý kiến trái chiều để đưa ra verdict.

---

## 🔄 Chế Độ Chạy Song Song: Mock & Real API

Để hệ thống hoạt động ổn định và có thể kiểm thử offline dễ dàng mà không tốn chi phí API, Swarm Engine tự động định tuyến thông minh:
*   **Khi THIẾU `GEMINI_API_KEY`**: Kích hoạt **Mock Debate Simulation (`src/mock_debate.py`)** sinh hội thoại typewriter line-by-line ngẫu nhiên nhưng bám sát chặt chẽ nhân cách của 10 Agents (ví dụ: Chuyên gia kỹ thuật phân tích chỉ số RSI, Chuyên gia Web3 kêu gọi HODL). Cấu trúc JSON trả ra khớp 100% định dạng của Real Agent để Frontend render mượt mà.
*   **Khi CÓ `GEMINI_API_KEY`**: Chạy đồ thị LangGraph thực tế. 9 Specialists sử dụng **Gemini 1.5 Flash** (tối ưu tốc độ, chi phí) và Moderator sử dụng **Gemini 1.5 Pro** (tối ưu lập luận logic).

---

## 📊 Báo Cáo Chi Phí & Context Caching

*   **Chi phí chuẩn**: Khoảng **~$0.0106** cho 1 phiên tranh luận 3 vòng đầy đủ (9 Specialists Flash + 1 Moderator Pro).
*   **Tối ưu hóa Caching**: Bằng cách sử dụng **Gemini Context Caching** cho các System Instruction dài cố định của 10 nhân vật, lượng token đầu vào được giảm 50%, giúp hạ chi phí xuống chỉ còn **~$0.006** cho mỗi lượt tranh luận ($18 cho 3,000 phiên chạy hàng tháng).

---

## 🚀 Hướng Dẫn CLI & Khởi Chạy

### 1. Cài đặt dependencies độc lập
```bash
# Đứng tại be/swarm-engine/
pip install -r requirements.txt
```

### 2. Thực thi CLI
Chạy thử nghiệm quét tranh luận cho một mã tài sản thông qua giao diện dòng lệnh:
```bash
python src/main.py --ticker BTC-USD --price 67250.45 --category CRYPTO
```
Chương trình sẽ tự động truy vấn SQLite/pgvector tìm sự kiện tương quan và bắt đầu in luồng log tranh luận ra `stdout` dạng JSON chunk-by-chunk.

### 3. Kiểm thử Engine
Chạy unit test luồng hoạt động độc lập của swarm-engine:
```bash
python test_engine.py
```
