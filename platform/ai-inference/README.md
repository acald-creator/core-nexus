# AI Inference Server

FastAPI triage enrichment for Wazuh, Suricata, Zeek, Falco, Tetragon, Vector-routed, and Athena-labeled events. Scores alerts and persists results so the API gateway can serve Console deep-links (`GET /api/v1/alerts/{id}/triage`).

This is a **NumPy baseline** (v1.1.0), not a production LLM runtime. Hardware scan endpoints recommend engines; they do not load vLLM/llama.cpp yet. Containment wording always requires **human approval**.

## Ingest paths

| Profile | How events arrive |
| --- | --- |
| Thin (`overlays/r2`) | Direct `POST /v1/triage` or gateway on-demand scoring |
| Compose-your-own (`overlays/hybrid-sensor`, ADR 0011) | Vector HTTP sink → `POST /v1/triage` (tags `nexus.source`) |
| Full SIEM (`overlays/test`) | Gateway may POST matching Wazuh alert on triage lookup miss |

Persistence: SQLite (`NEXUS_AI_DB_PATH` or `./data/triage.db`). This is the **security event store** for thin and hybrid labs; Wazuh indexer remains the store for full SIEM labs.

## Components

| File | Role |
|------|------|
| `main.py` | FastAPI routes |
| `triage.py` | Feature pack + scoring (severity, ports/rules, text, Suricata category / Wazuh groups+MITRE, Athena label) |
| `store.py` | SQLite persistence (`NEXUS_AI_DB_PATH` or `./data/triage.db`) |
| `preflight.py` | Optional hardware preflight helper |
| `Dockerfile` | Image build; persists DB under `/data` |

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Service status |
| GET | `/health` | Liveness + record count |
| POST | `/v1/triage` | Score one event or a batch; persist |
| GET | `/v1/triage/{event_id}` | Lookup by alert/event id (gateway uses this) |
| GET | `/v1/hardware` | Advisory CPU/GPU scan |
| GET | `/v1/models` | Active model metadata |
| GET | `/v1/memory` | Persistence stats |
| POST | `/v1/memory/query` | Keyword overlap over recent triage text |

Responses include both snake_case and Console camelCase aliases (`confidenceScore`, `recommendedAction`, `reasoningExcerpt`).

Athena-labeled traffic prefers `needs_human_review` over auto-contain language.

## Local run

```bash
cd platform/ai-inference
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
docker build -t local/ai-inference:latest platform/ai-inference/
docker run --rm -p 8000:8000 -v ai-inference-data:/data local/ai-inference:latest
```

## Gateway contract

`platform/api-gateway` maps service fields via `to_console_triage`, then validates `TriageResponse`. On GET miss, the alerts route may POST the matching Wazuh alert for on-demand scoring when Wazuh is deployed. Hybrid labs without Wazuh rely on Vector → `POST /v1/triage` (ADR 0011); gateway alert-list adapter is follow-on H2.
