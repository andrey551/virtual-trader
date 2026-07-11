FROM python:3.12-slim

WORKDIR /app

# Install docker CLI binary
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-26.1.4.tgz | tar -xz -C /tmp && \
    mv /tmp/docker/docker /usr/local/bin/docker && \
    rm -rf /tmp/docker && \
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*


# Install dependencies
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt

COPY . /app

# Set python path to allow imports inside the container
ENV PYTHONPATH=/app

# Expose port 8002 for FastAPI service
EXPOSE 8002

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8002"]


