import os
import subprocess
import time
import re
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from triage import TriageModel

app = FastAPI(
    title="Underground Nexus AI Inference Server",
    description="REST API interface for security event triage, hardware scanning, and MLOps metrics.",
    version="1.0.0"
)

# Instantiate triage model
triage_model = TriageModel()

# Mock RAG Vector Memory
vector_memory: List[Dict[str, Any]] = []

from pydantic import BaseModel, Field

class EventPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: str(time.time()))
    timestamp: str = None
    alert: Dict[str, Any] = None
    dest_port: int = None
    rule: Dict[str, Any] = None
    data: Dict[str, Any] = None
    
    class Config:
        extra = "allow"

class RAGQuery(BaseModel):
    query_text: str
    limit: int = 3

@app.get("/")
def read_root():
    return {
        "service": "Underground Nexus AI Inference Layer",
        "status": "operational",
        "phase": 1,
        "supported_endpoints": [
            "/v1/triage",
            "/v1/hardware",
            "/v1/models",
            "/v1/memory"
        ]
    }

from fastapi import FastAPI, HTTPException, Request

@app.post("/v1/triage")
async def triage_event(request: Request):
    raw_body = await request.body()
    print("RAW_BODY_START:", raw_body, "RAW_BODY_END", flush=True)
    try:
        import json
        payload = json.loads(raw_body)
    except Exception as e:
        print("JSON parse error:", e, flush=True)
        return {"status": "error", "reason": str(e)}

    # Handle Vector batching (List of events) or single events
    events = payload if isinstance(payload, list) else [payload]
    
    results = []
    for event in events:
        triage_output = triage_model.triage_event(event)
        triage_output["saved_at"] = time.time()
        vector_memory.append(triage_output)
        results.append(triage_output)
    
    return results if isinstance(payload, list) else results[0]

@app.get("/v1/hardware")
def get_hardware_status():
    """Scan node for hardware capability (e.g. GPUs, CPU details)."""
    has_nvidia_gpu = False
    gpu_details = "None"
    
    # Check for Nvidia GPU using device files or nvidia-smi
    if os.path.exists("/dev/nvidia0") or os.path.exists("/dev/nvidiactl"):
        has_nvidia_gpu = True
        try:
            # Query nvidia-smi for GPU name
            smi_output = subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], stderr=subprocess.DEVNULL)
            gpu_details = smi_output.decode("utf-8").strip()
        except Exception:
            gpu_details = "Nvidia Driver Device Detected (nvidia-smi not in PATH)"
            
    # Read CPU details from /proc/cpuinfo
    cpu_model = "Unknown CPU"
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    cpu_model = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    # Select engine recommendation based on scanned hardware
    recommended_engine = "llama.cpp (Quantized CPU Inference)"
    if has_nvidia_gpu:
        recommended_engine = "vLLM (High-Throughput GPU Inference)"

    return {
        "timestamp": time.time(),
        "scanned_cpu": cpu_model,
        "nvidia_gpu_available": has_nvidia_gpu,
        "gpu_details": gpu_details,
        "recommended_serving_engine": recommended_engine,
        "supported_formats": ["FP8", "AWQ", "GGUF"] if has_nvidia_gpu else ["GGUF"]
    }

@app.get("/v1/models")
def get_models():
    return {
        "active_model": {
            "name": triage_model.model_name,
            "version": triage_model.model_version,
            "digest": triage_model.model_digest,
            "threshold": triage_model.threshold,
            "inputs": ["Suricata", "Wazuh"]
        },
        "available_models": [
            {
                "name": "nexus-triage-baseline",
                "version": "1.0.0",
                "status": "active"
            },
            {
                "name": "nexus-triage-deep-onnx",
                "version": "2.0.0-draft",
                "status": "testing"
            }
        ]
    }

@app.post("/v1/memory/query")
def query_memory(query: RAGQuery):
    """Simple mockup RAG semantic search based on keyword overlap in logs."""
    # Clean up non-alphanumeric characters for robust word matching
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', ' ', query.query_text.lower())
    query_words = set(clean_query.split())
    matches = []
    
    for item in vector_memory:
        reason = item.get("reason", "").lower()
        rec = item.get("recommended_action", "").lower()
        combined_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', reason + " " + rec)
        item_words = set(combined_text.split())
        
        overlap = len(query_words.intersection(item_words))
        if overlap > 0:
            matches.append((overlap, item))
            
    # Sort matches by highest word overlap score
    matches.sort(key=lambda x: x[0], reverse=True)
    results = [item for _, item in matches[:query.limit]]
    
    return {
        "query": query.query_text,
        "results_found": len(results),
        "matches": results
    }

@app.get("/v1/memory")
def get_memory_stats():
    return {
        "total_records_stored": len(vector_memory),
        "recent_records": vector_memory[-5:] if vector_memory else []
    }
