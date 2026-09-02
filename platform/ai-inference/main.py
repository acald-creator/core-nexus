"""Underground Nexus AI Inference — triage enrichment API (E0–E2)."""
from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from store import TriageStore
from triage import TriageModel

app = FastAPI(
    title="Underground Nexus AI Inference Server",
    description="Security event triage enrichment (Suricata/Wazuh/Athena). Human approval required for response.",
    version="1.1.0",
)

triage_model = TriageModel()
store = TriageStore()


class RAGQuery(BaseModel):
    query_text: str
    limit: int = Field(default=3, ge=1, le=50)


@app.get("/")
def read_root():
    return {
        "service": "Underground Nexus AI Inference Layer",
        "status": "operational",
        "phase": 1,
        "model": {
            "name": triage_model.model_name,
            "version": triage_model.model_version,
        },
        "supported_endpoints": [
            "/health",
            "/v1/triage",
            "/v1/triage/recent",
            "/v1/triage/{event_id}",
            "/v1/hardware",
            "/v1/models",
            "/v1/memory",
            "/v1/memory/query",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok", "records": store.count()}


def _triage_and_persist(event: dict[str, Any]) -> dict[str, Any]:
    result = triage_model.triage_event(event)
    result["saved_at"] = time.time()
    return store.upsert(result)


@app.post("/v1/triage")
async def triage_event(request: Request):
    """Score one event or a batch; persist each result (E0/E1)."""
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}") from exc

    events = payload if isinstance(payload, list) else [payload]
    if not events:
        raise HTTPException(status_code=400, detail="empty event payload")

    results = []
    for event in events:
        if not isinstance(event, dict):
            raise HTTPException(status_code=400, detail="each event must be an object")
        results.append(_triage_and_persist(event))

    return results if isinstance(payload, list) else results[0]


@app.get("/v1/triage/recent")
def list_recent_triage(limit: int = 100):
    """List persisted triage results, newest first (for gateway alerts + purple eval)."""
    return {"total": store.count(), "results": store.recent(limit=limit)}


@app.get("/v1/triage/{event_id}")
def get_triage(event_id: str):
    """Lookup a persisted triage result by source event / alert id (E0)."""
    result = store.get(event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No triage result available")
    return result


@app.get("/v1/hardware")
def get_hardware_status():
    """Scan node for hardware capability (advisory only until a real engine is loaded)."""
    has_nvidia_gpu = False
    gpu_details = "None"

    if os.path.exists("/dev/nvidia0") or os.path.exists("/dev/nvidiactl"):
        has_nvidia_gpu = True
        try:
            smi_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL,
            )
            gpu_details = smi_output.decode("utf-8").strip()
        except Exception:
            gpu_details = "Nvidia Driver Device Detected (nvidia-smi not in PATH)"

    cpu_model = "Unknown CPU"
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if "model name" in line:
                    cpu_model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass

    recommended_engine = "llama.cpp (Quantized CPU Inference)"
    if has_nvidia_gpu:
        recommended_engine = "vLLM (High-Throughput GPU Inference)"

    return {
        "timestamp": time.time(),
        "scanned_cpu": cpu_model,
        "nvidia_gpu_available": has_nvidia_gpu,
        "gpu_details": gpu_details,
        "recommended_serving_engine": recommended_engine,
        "supported_formats": ["FP8", "AWQ", "GGUF"] if has_nvidia_gpu else ["GGUF"],
        "note": "Recommendation only — current triage uses NumPy baseline v1.1.0, not LLM runtimes.",
    }


@app.get("/v1/models")
def get_models():
    return {
        "active_model": {
            "name": triage_model.model_name,
            "version": triage_model.model_version,
            "digest": triage_model.model_digest,
            "threshold": triage_model.threshold,
            "inputs": ["Suricata", "Wazuh", "Athena-labeled traffic"],
        },
        "available_models": [
            {
                "name": triage_model.model_name,
                "version": triage_model.model_version,
                "status": "active",
            }
        ],
    }


@app.post("/v1/memory/query")
def query_memory(query: RAGQuery):
    results = store.search(query.query_text, limit=query.limit)
    return {
        "query": query.query_text,
        "results_found": len(results),
        "matches": results,
    }


@app.get("/v1/memory")
def get_memory_stats():
    return {
        "total_records_stored": store.count(),
        "recent_records": store.recent(5),
        "backend": "sqlite",
        "db_path": str(store.db_path),
    }
