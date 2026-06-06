# Sử dụng image chính thức của Microsoft Playwright cho Python
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Sao chép và cài đặt các dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép file server.py và thư mục src vào image
COPY server.py .
COPY src/ ./src/

# Thiết lập entrypoint chạy server thông qua stdio
ENTRYPOINT ["python", "server.py"]
