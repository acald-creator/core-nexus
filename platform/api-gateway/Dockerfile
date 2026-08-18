# Stage 1: Dependencies
FROM python:3.11-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application
FROM python:3.11-slim AS runtime
WORKDIR /app

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 3100

ENV NEXUS_GW_PORT=3100
ENV NEXUS_GW_SERVICE_REGISTRY_PATH=/app/config/services.json

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3100"]
