# AI Inference Server

This directory contains the Python-based AI-triage enrichment service (FastAPI) which processes security event logs from Wazuh and Suricata, performs hardware-aware pre-flight checks, and provides local vector RAG memory.

## Code Components

- [main.py](file:///home/acald-creator/go/src/github.com/acald-creator/core-nexus/platform/ai-inference/main.py): Application entrypoint exposing API routing.
- [triage.py](file:///home/acald-creator/go/src/github.com/acald-creator/core-nexus/platform/ai-inference/triage.py): Ingestion and scoring model implementation using NumPy.
- [requirements.txt](file:///home/acald-creator/go/src/github.com/acald-creator/core-nexus/platform/ai-inference/requirements.txt): List of Python dependencies.
- [Dockerfile](file:///home/acald-creator/go/src/github.com/acald-creator/core-nexus/platform/ai-inference/Dockerfile): Container builds file.

## Core API Endpoints

- **GET `/`**: Service configuration and operational status check.
- **POST `/v1/triage`**: Ingest security events (Suricata or Wazuh alert logs) and output a standardized threat score, categorization, and action response.
- **GET `/v1/hardware`**: Pre-flight node hardware scanning. Automatically detects CPU details and NVIDIA GPUs (`/dev/nvidia*`), recommending the appropriate inference backend (GGUF CPU vs GPU-accelerated FP8/AWQ).
- **GET `/v1/models`**: Active and testing model metadata list.
- **POST `/v1/memory/query`**: Local vector memory query (semantic/RAG overlap logic on alerts).
- **GET `/v1/memory`**: View statistics on triaged history.

## Local Building & Running

### Building local Docker Image
```bash
docker build -t local/ai-inference:latest platform/ai-inference/
```

### Running Locally
```bash
pip install -r platform/ai-inference/requirements.txt
uvicorn platform.ai-inference.main:app --reload
```
