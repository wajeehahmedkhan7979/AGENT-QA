FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS=ignore::UserWarning

COPY apps/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/backend /app/backend
COPY runner /app/runner

ENV PYTHONPATH=/app/backend:/app

CMD ["rq", "worker", "runs"]
