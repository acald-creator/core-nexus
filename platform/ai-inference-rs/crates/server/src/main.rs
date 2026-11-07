//! Underground Nexus AI Inference — HTTP triage API.
//!
//! Rust/axum port of `platform/ai-inference/main.py`. Routes, status codes, and
//! JSON response shapes match the FastAPI service 1:1 so the API gateway's
//! `to_console_triage` mapping keeps working unchanged. See the crate README and
//! `PARITY.md` for the invariant: the Python service is the oracle.
//!
//! Scoring lives in [`nexus_triage`]; persistence in [`nexus_triage_store`].
//! This binary only wires HTTP to those two crates.

use std::net::SocketAddr;
use std::path::Path as FsPath;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use axum::{
    body::Bytes,
    extract::{Path, Query, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::Deserialize;
use serde_json::{json, Value};

use nexus_triage::TriageModel;
use nexus_triage_store::{StoreError, TriageStore};

/// Shared, immutable-after-startup application state (mirrors the module-level
/// `triage_model` and `store` singletons in main.py:22-23).
struct AppState {
    model: TriageModel,
    store: TriageStore,
}

/// Current Unix time in seconds, used wherever Python calls `time.time()`.
fn now_unix() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

// ---------------------------------------------------------------------------
// Error type — mirrors FastAPI's HTTPException -> {"detail": "..."} body.
// ---------------------------------------------------------------------------

struct ApiError {
    status: StatusCode,
    detail: String,
}

impl ApiError {
    fn bad_request(detail: impl Into<String>) -> Self {
        ApiError {
            status: StatusCode::BAD_REQUEST,
            detail: detail.into(),
        }
    }
    fn not_found(detail: impl Into<String>) -> Self {
        ApiError {
            status: StatusCode::NOT_FOUND,
            detail: detail.into(),
        }
    }
    /// 500 handler. PARITY + security: the underlying error is logged
    /// server-side but NOT returned to the client. Python/Starlette's default
    /// 500 body is a generic message, and echoing the SQLite error would leak
    /// implementation detail. Bodies differ only in shape (JSON `{"detail":...}`
    /// here vs Starlette's plain text); see PARITY.md.
    fn internal(err: impl std::fmt::Display) -> Self {
        tracing::error!(error = %err, "internal server error");
        ApiError {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            detail: "Internal Server Error".to_string(),
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, Json(json!({ "detail": self.detail }))).into_response()
    }
}

impl From<StoreError> for ApiError {
    fn from(e: StoreError) -> Self {
        ApiError::internal(e)
    }
}

// ---------------------------------------------------------------------------
// Handlers (one per route in main.py)
// ---------------------------------------------------------------------------

/// `GET /` — service status (main.py:31-51).
async fn read_root(State(s): State<Arc<AppState>>) -> Json<Value> {
    Json(json!({
        "service": "Underground Nexus AI Inference Layer",
        "status": "operational",
        "phase": 1,
        "model": {
            "name": s.model.model_name,
            "version": s.model.model_version,
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
    }))
}

/// `GET /health` — liveness + record count (main.py:54-56).
async fn health(State(s): State<Arc<AppState>>) -> Result<Json<Value>, ApiError> {
    Ok(Json(json!({ "status": "ok", "records": s.store.count()? })))
}

/// Score one event and persist it (port of `_triage_and_persist`, main.py:59-62).
fn triage_and_persist(s: &AppState, event: &Value) -> Result<Value, StoreError> {
    let now = now_unix();
    let result = s.model.triage_event(event, now);
    let mut value = serde_json::to_value(result).expect("TriageResult serializes");
    // main.py:61 sets saved_at = time.time() before persisting.
    value["saved_at"] = json!(now);
    s.store.upsert(value, now)
}

/// `POST /v1/triage` — score one event or a batch (main.py:65-84).
async fn triage(State(s): State<Arc<AppState>>, body: Bytes) -> Result<Json<Value>, ApiError> {
    let payload: Value = serde_json::from_slice(&body)
        .map_err(|e| ApiError::bad_request(format!("invalid JSON: {e}")))?;

    let is_array = payload.is_array();
    let events: Vec<Value> = if is_array {
        payload.as_array().cloned().unwrap_or_default()
    } else {
        vec![payload]
    };
    if events.is_empty() {
        return Err(ApiError::bad_request("empty event payload"));
    }

    let mut results = Vec::with_capacity(events.len());
    for event in &events {
        if !event.is_object() {
            return Err(ApiError::bad_request("each event must be an object"));
        }
        results.push(triage_and_persist(&s, event)?);
    }

    // Return a bare object for a single event, an array for a batch (main.py:84).
    if is_array {
        Ok(Json(Value::Array(results)))
    } else {
        Ok(Json(results.into_iter().next().expect("one result")))
    }
}

#[derive(Deserialize)]
struct RecentParams {
    #[serde(default = "default_recent_limit")]
    limit: i64,
}
fn default_recent_limit() -> i64 {
    100
}

/// `GET /v1/triage/recent` — persisted results, newest first (main.py:87-90).
async fn list_recent(
    State(s): State<Arc<AppState>>,
    Query(p): Query<RecentParams>,
) -> Result<Json<Value>, ApiError> {
    Ok(Json(json!({
        "total": s.store.count()?,
        "results": s.store.recent(p.limit)?,
    })))
}

/// `GET /v1/triage/{event_id}` — lookup by id, 404 on miss (main.py:93-99).
async fn get_triage(
    State(s): State<Arc<AppState>>,
    Path(event_id): Path<String>,
) -> Result<Json<Value>, ApiError> {
    match s.store.get(&event_id)? {
        Some(result) => Ok(Json(result)),
        None => Err(ApiError::not_found("No triage result available")),
    }
}

/// `GET /v1/hardware` — advisory CPU/GPU scan (main.py:102-141).
async fn hardware() -> Json<Value> {
    let has_nvidia_gpu = FsPath::new("/dev/nvidia0").exists() || FsPath::new("/dev/nvidiactl").exists();

    let gpu_details = if has_nvidia_gpu {
        match std::process::Command::new("nvidia-smi")
            .args(["--query-gpu=name", "--format=csv,noheader"])
            .output()
        {
            Ok(out) if out.status.success() => {
                String::from_utf8_lossy(&out.stdout).trim().to_string()
            }
            _ => "Nvidia Driver Device Detected (nvidia-smi not in PATH)".to_string(),
        }
    } else {
        "None".to_string()
    };

    // /proc/cpuinfo only exists on Linux; elsewhere this falls back like Python's
    // bare `except OSError`.
    let cpu_model = std::fs::read_to_string("/proc/cpuinfo")
        .ok()
        .and_then(|text| {
            text.lines()
                .find(|l| l.contains("model name"))
                .and_then(|l| l.split_once(':'))
                .map(|(_, v)| v.trim().to_string())
        })
        .unwrap_or_else(|| "Unknown CPU".to_string());

    let recommended_engine = if has_nvidia_gpu {
        "vLLM (High-Throughput GPU Inference)"
    } else {
        "llama.cpp (Quantized CPU Inference)"
    };
    let supported_formats = if has_nvidia_gpu {
        vec!["FP8", "AWQ", "GGUF"]
    } else {
        vec!["GGUF"]
    };

    Json(json!({
        "timestamp": now_unix(),
        "scanned_cpu": cpu_model,
        "nvidia_gpu_available": has_nvidia_gpu,
        "gpu_details": gpu_details,
        "recommended_serving_engine": recommended_engine,
        "supported_formats": supported_formats,
        "note": "Recommendation only — current triage uses NumPy baseline v1.1.0, not LLM runtimes.",
    }))
}

/// `GET /v1/models` — active model metadata (main.py:144-161).
async fn models(State(s): State<Arc<AppState>>) -> Json<Value> {
    Json(json!({
        "active_model": {
            "name": s.model.model_name,
            "version": s.model.model_version,
            "digest": s.model.model_digest,
            "threshold": s.model.threshold,
            "inputs": ["Suricata", "Wazuh", "Athena-labeled traffic"],
        },
        "available_models": [{
            "name": s.model.model_name,
            "version": s.model.model_version,
            "status": "active",
        }],
    }))
}

#[derive(Deserialize)]
struct RagQuery {
    query_text: String,
    #[serde(default = "default_rag_limit")]
    limit: i64,
}
fn default_rag_limit() -> i64 {
    3
}

/// `POST /v1/memory/query` — keyword overlap over recent triage text (main.py:164-171).
///
/// PARITY: pydantic enforces `1 <= limit <= 50` and would 422 out-of-range
/// values; here the store clamps instead, so an out-of-range limit is accepted
/// and clamped rather than rejected. Behaviour matches for in-range values.
async fn memory_query(
    State(s): State<Arc<AppState>>,
    Json(q): Json<RagQuery>,
) -> Result<Json<Value>, ApiError> {
    let matches = s.store.search(&q.query_text, q.limit)?;
    Ok(Json(json!({
        "query": q.query_text,
        "results_found": matches.len(),
        "matches": matches,
    })))
}

/// `GET /v1/memory` — persistence stats (main.py:174-180).
async fn memory_stats(State(s): State<Arc<AppState>>) -> Result<Json<Value>, ApiError> {
    Ok(Json(json!({
        "total_records_stored": s.store.count()?,
        "recent_records": s.store.recent(5)?,
        "backend": "sqlite",
        "db_path": s.store.db_path().to_string_lossy(),
    })))
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .init();

    let store = TriageStore::from_env().unwrap_or_else(|e| {
        panic!("failed to open triage store: {e}");
    });
    let state = Arc::new(AppState {
        model: TriageModel::new(),
        store,
    });

    let app = Router::new()
        .route("/", get(read_root))
        .route("/health", get(health))
        .route("/v1/triage", post(triage))
        .route("/v1/triage/recent", get(list_recent))
        .route("/v1/triage/{event_id}", get(get_triage))
        .route("/v1/hardware", get(hardware))
        .route("/v1/models", get(models))
        .route("/v1/memory/query", post(memory_query))
        .route("/v1/memory", get(memory_stats))
        .with_state(state);

    // Port matches the Python container default (uvicorn ... --port 8000).
    let port: u16 = std::env::var("NEXUS_AI_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8000);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .unwrap_or_else(|e| panic!("failed to bind {addr}: {e}"));
    tracing::info!(%addr, "ai-inference (rust) listening");

    axum::serve(listener, app)
        .await
        .expect("server error");
}
