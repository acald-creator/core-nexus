# AI Inference — Rust port (`ai-inference-rs`)

A faithful Rust re-implementation of the Python triage service in
[`../ai-inference/`](../ai-inference/). Same endpoints, same JSON shapes, same
scores and labels.

> **Scope (do not over-claim).** This is a Rust rewrite of the **Phase 1 NumPy
> baseline** scorer described in `docs/architecture/06-ai-soc-inference-engine.md`
> §1. It is *not* the Phase 3 "Rust service with ONNX Runtime inside a gVisor
> sandbox" target. No ML runtime is loaded; scoring is a fixed linear model.
> Containment wording still always requires **human approval**.

## Why both exist

The port is a Rust learning vehicle and a step toward the documented Rust future
state. The Python service stays in the tree as the **behavioural oracle**: if the
two disagree, Python is right until a change is made deliberately in both. See
[`PARITY.md`](PARITY.md) for the rule that keeps them in lockstep.

## Layout (mirrors the `athena-agents` workspace)

| Crate | Rust | Ports | Teaches |
|---|---|---|---|
| `crates/triage` | `nexus-triage` (lib) | [`triage.py`](../ai-inference/triage.py) | structs, enums, pattern matching, `Option`, traits, unit tests |
| `crates/store` | `nexus-triage-store` (lib) | [`store.py`](../ai-inference/store.py) | `rusqlite`, error enums + `From`, `Mutex` |
| `crates/server` | `ai-inference` (bin) | [`main.py`](../ai-inference/main.py) | `axum`, `tokio`, extractors, `IntoResponse` |

The scorer has **no I/O and no async** — it is the best file to read first.

## Run

```bash
cd platform/ai-inference-rs
cargo run -p ai-inference        # serves on 0.0.0.0:8000 (NEXUS_AI_PORT to override)
```

```bash
cargo test --workspace           # runs the ported oracle tests
```

Environment variables match the Python service: `NEXUS_AI_DB_PATH`, or
`NEXUS_AI_DATA_DIR` (default `./data`), select the SQLite file.

## API (identical to the Python service)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Service status |
| GET | `/health` | Liveness + record count |
| POST | `/v1/triage` | Score one event or a batch; persist |
| GET | `/v1/triage/recent` | Newest-first persisted results (`?limit=`) |
| GET | `/v1/triage/{event_id}` | Lookup by alert/event id |
| GET | `/v1/hardware` | Advisory CPU/GPU scan |
| GET | `/v1/models` | Active model metadata |
| GET | `/v1/memory` | Persistence stats |
| POST | `/v1/memory/query` | Keyword overlap over recent triage text |

Responses carry both snake_case and Console camelCase aliases
(`confidenceScore`, `recommendedAction`, `reasoningExcerpt`), same as Python.

## Verifying parity by hand

The Python and Rust services should return the same `score`, `label`, and
`features_used` for the same event. Quick cross-check:

```bash
# Python (needs numpy): prints a scored result
cd ../ai-inference && python3 -c "import json,triage; print(json.dumps(triage.TriageModel().triage_event({'id':'x','rule':{'id':5710,'level':10,'description':'authentication failed','groups':['authentication_failed'],'mitre':{'id':['T1110']}}}), indent=2))"
```

The ported tests in `crates/triage/src/lib.rs` and `crates/store/src/lib.rs`
already pin these values; two extra tests (`parity_*_score_exact`) lock exact
scores so arithmetic drift fails the build.
