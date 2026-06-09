FROM python:3.12-slim

WORKDIR /app

# Install basic system packages, curl, and Docker CLI (for Docker-out-of-Docker stdio MCP connection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends \
    docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies for backend-core
COPY backend-core/requirements.txt /app/backend-core/requirements.txt
RUN pip install --no-cache-dir -r /app/backend-core/requirements.txt

# Copy source code files into their relative workspaces
COPY backend-core /app/backend-core

# Set working directory to backend-core to run uvicorn
WORKDIR /app/backend-core

EXPOSE 8000

# Run Uvicorn production server exposing port 8000
ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
