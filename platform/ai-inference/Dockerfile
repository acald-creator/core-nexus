FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY triage.py .
COPY store.py .
COPY preflight.py .

RUN mkdir -p /data

ENV NEXUS_AI_DB_PATH=/data/triage.db

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /data

USER 10001

VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
