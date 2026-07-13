FROM python:3.12-slim

WORKDIR /app

COPY backend-core/requirements.txt ./backend_requirements.txt
COPY accuracy-evaluator/requirements.txt ./evaluator_requirements.txt

RUN pip install --no-cache-dir -r backend_requirements.txt
RUN pip install --no-cache-dir -r evaluator_requirements.txt

COPY accuracy-evaluator/src /app/accuracy_evaluator
COPY backend-core /app/backend-core

ENV PYTHONPATH="/app:/app/backend-core"

CMD ["python", "-u", "accuracy_evaluator/main.py"]

