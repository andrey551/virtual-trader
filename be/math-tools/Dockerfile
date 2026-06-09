FROM python:3.12-slim

WORKDIR /app

# Install basic compile-time tools for numpy/scipy/statsmodels if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# MCP server running over stdio
ENTRYPOINT ["python", "server.py"]
