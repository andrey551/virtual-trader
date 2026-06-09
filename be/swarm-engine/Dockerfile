FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Set python path to allow imports inside the container
ENV PYTHONPATH=/app

ENTRYPOINT ["python", "src/main.py"]
