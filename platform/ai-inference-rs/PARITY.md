# Parity contract — Python oracle ↔ Rust port

This document is the rule that keeps `platform/ai-inference/` (Python) and
`platform/ai-inference-rs/` (Rust) from drifting. Read it before changing either.

## The invariant

**The Python service is the behavioural oracle.** For the same input, both
services must return the same `score`, `label`, `features_used`, `event_type`,
and the same JSON field set. When they disagree, the Python result is correct
until a change is made **deliberately in both**.

## Rule for any behaviour change

A change to scoring, feature extraction, labels, storage, or an endpoint is only
complete when all four of these land together, in one change:

1. The Python source (`triage.py` / `store.py` / `main.py`).
2. The Rust source (the matching crate under `crates/`).
3. The Python tests (`test_triage.py`).
4. The Rust tests (the `#[cfg(test)]` modules).

If you can only do one side now, do not merge the behaviour change — note it as a
known divergence here instead, so the next reader knows the oracle moved.

## Where the subtle parity decisions live

These are the places a careless port drifts. Each is marked with a `// PARITY:`
comment at its site in the Rust source:

| Behaviour | Python | Rust |
|---|---|---|
| `dict.get(k) or default` truthiness (0/""/[]/{} are falsy) | throughout | `truthy` / `get_truthy` in `crates/triage/src/lib.rs` |
| Label band: `score < 0.75` **or** Athena-labeled → review | `triage.py:335` | `classify` |
| Suricata severity keys off a **non-empty** alert object | `triage.py:133` | `suricata_features` |
| Wazuh inline MITRE list keeps **all** items (no truthy filter) | `triage.py:256-259` | `wazuh_features` (contrast with `collect_mitre_ids`) |
| `round(x, 4)` is banker's rounding | `triage.py:361` | `round4` |
| JSON object key order preserved | dict insertion order | `serde_json` `preserve_order` feature |
| `score`/`confidenceScore` fallback uses truthiness (0 falls through) | `store.py:59` | `truthy_f64` in `crates/store/src/lib.rs` |
| `recent` clamp `[1,500]`, `search` output clamp `[1,50]` | `store.py:90,130` | `recent` / `search` |

## Known divergences

**All confirmed divergences are on malformed-input error paths.** The happy path
— scores, labels, `features_used`, stored payloads, and every well-formed
response — is identical and covered by the ported tests. These remain divergent
on purpose: reproducing them would mean copying Python's accidental
uncaught-exception behaviour or rebuilding pydantic's validation machinery.

1. **Non-integer strings in `severity` / `dest_port` / `level`.** Python wraps
   only `rule.id` in try/except (triage.py:213-215); the other three call a bare
   `int()` that RAISES on a non-numeric string, surfacing as **HTTP 500**. Rust's
   `get_int_or` is lenient for all four and scores the event (**HTTP 200**). Rust
   also accepts float strings like `"2.5"` (→ `2`), which Python's `int()`
   rejects. We keep the robust Rust behaviour. (triage lens; findings 1, 9.)
2. **`POST /v1/memory/query` `limit` outside `1..=50`.** Python (pydantic
   `Field(ge=1, le=50)`) returns **HTTP 422**; Rust accepts and clamps to the
   range (**HTTP 200**). In-range behaviour is identical. (findings 2, 6.)
3. **Non-integer `limit` query param on `GET /v1/triage/recent`.** Python returns
   **422**; axum's `Query` extractor rejects with **400** (plain text). Valid
   integers behave identically. (findings 3, 7.)
4. **Malformed JSON body on `POST /v1/memory/query`.** Python (pydantic body
   model) returns **422**; axum's `Json` extractor returns **400**. (finding 5.)
5. **500 response body shape.** Starlette's default 500 is plain text
   `Internal Server Error`; Rust returns JSON `{"detail":"Internal Server Error"}`.
   Neither leaks internals — the Rust server now logs the underlying error and
   returns a generic message (fixed; findings 4, 8). Only the wrapper shape
   differs.
6. **`timestamp` fallback string** for an event with no timestamp: both stringify
   the current Unix time, but Python's `str(float)` and Rust's `format!` may
   differ in trailing digits. Not part of scoring; never asserted.

Resolved during review: `feature_meta.suricata_signature_id` now matches Python's
`a or b` semantics when both `signature_id` and `sid` are falsy (finding 10).

## How to re-verify parity

```bash
# Rust side (ported oracle tests, incl. exact-score anchors)
cd platform/ai-inference-rs && cargo test --workspace

# Python side (needs numpy + pytest in a venv)
cd platform/ai-inference && python3 -m pytest -q test_triage.py
```

Both suites assert the same cases. The Rust `parity_suricata_score_exact` and
`parity_wazuh_score_exact` tests additionally pin the exact scores
(`0.97`, `0.7833`) that the Python oracle produces for those inputs.
