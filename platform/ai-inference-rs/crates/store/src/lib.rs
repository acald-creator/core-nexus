//! SQLite persistence for triage results — Rust port of
//! `platform/ai-inference/store.py`.
//!
//! This is the **security event store** for thin and hybrid SOC labs (ADR 0011).
//! It persists one JSON payload per source event, keyed by `source_event_id`,
//! and supports newest-first listing plus a pre-embeddings keyword search.
//!
//! # Parity notes
//!
//! - Works on [`serde_json::Value`] objects, exactly like the Python code works
//!   on `dict[str, Any]`, so stored payloads are byte-compatible.
//! - The table schema, upsert SQL, and the `[1, 500]` / `[1, 50]` clamps are
//!   identical to `store.py`.
//! - Concurrency: Python opens a fresh connection per call under a module-global
//!   lock. We keep a single connection behind a [`Mutex`], which serializes
//!   access the same way with less overhead. Behaviour is unchanged.

use std::path::{Path, PathBuf};
use std::sync::Mutex;

use rusqlite::{params, Connection, OptionalExtension};
use serde_json::Value;

/// Errors surfaced by the store. The server maps these onto HTTP responses.
#[derive(Debug)]
pub enum StoreError {
    /// `upsert` was handed a result with no usable `source_event_id`/`id`.
    MissingEventId,
    /// An underlying SQLite failure.
    Sqlite(rusqlite::Error),
    /// A payload failed to (de)serialize.
    Json(serde_json::Error),
}

impl std::fmt::Display for StoreError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StoreError::MissingEventId => write!(f, "triage result missing source_event_id"),
            StoreError::Sqlite(e) => write!(f, "sqlite error: {e}"),
            StoreError::Json(e) => write!(f, "json error: {e}"),
        }
    }
}

impl std::error::Error for StoreError {}

impl From<rusqlite::Error> for StoreError {
    fn from(e: rusqlite::Error) -> Self {
        StoreError::Sqlite(e)
    }
}

impl From<serde_json::Error> for StoreError {
    fn from(e: serde_json::Error) -> Self {
        StoreError::Json(e)
    }
}

/// Convenience result alias.
pub type Result<T> = std::result::Result<T, StoreError>;

/// Resolve the default DB path from the environment (port of `default_db_path`,
/// store.py:16-20): `NEXUS_AI_DB_PATH` if set and non-blank, else
/// `${NEXUS_AI_DATA_DIR:-./data}/triage.db`.
pub fn default_db_path() -> PathBuf {
    if let Ok(raw) = std::env::var("NEXUS_AI_DB_PATH") {
        let trimmed = raw.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    let dir = std::env::var("NEXUS_AI_DATA_DIR").unwrap_or_else(|_| "./data".to_string());
    PathBuf::from(dir).join("triage.db")
}

/// SQLite-backed triage result store.
pub struct TriageStore {
    db_path: PathBuf,
    conn: Mutex<Connection>,
}

impl TriageStore {
    /// Open (creating parent dirs) and initialise the schema at `db_path`.
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let db_path = db_path.as_ref().to_path_buf();
        if let Some(parent) = db_path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent).map_err(|e| {
                    StoreError::Sqlite(rusqlite::Error::ToSqlConversionFailure(Box::new(e)))
                })?;
            }
        }
        let conn = Connection::open(&db_path)?;
        let store = TriageStore {
            db_path,
            conn: Mutex::new(conn),
        };
        store.init_schema()?;
        Ok(store)
    }

    /// Open the store at [`default_db_path`].
    pub fn from_env() -> Result<Self> {
        Self::new(default_db_path())
    }

    /// The resolved on-disk path (echoed on `/v1/memory`).
    pub fn db_path(&self) -> &Path {
        &self.db_path
    }

    /// Create the table and the `saved_at` index (store.py:34-51).
    fn init_schema(&self) -> Result<()> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        conn.execute(
            "CREATE TABLE IF NOT EXISTS triage_results (
                source_event_id TEXT PRIMARY KEY,
                saved_at REAL NOT NULL,
                score REAL NOT NULL,
                label TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )",
            [],
        )?;
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_triage_saved_at ON triage_results(saved_at DESC)",
            [],
        )?;
        Ok(())
    }

    /// Insert or update one result (port of `upsert`, store.py:53-76).
    ///
    /// Mirrors the Python extraction order: `source_event_id`/`id` for the key,
    /// `saved_at` (falling back to `now_fallback`), `score`/`confidenceScore`
    /// for the indexed score, `label` (default `"unknown"`). The merged value —
    /// with `saved_at` and `source_event_id` written back — is stored as the
    /// payload and returned.
    pub fn upsert(&self, mut result: Value, now_fallback: f64) -> Result<Value> {
        let obj = result.as_object_mut().ok_or(StoreError::MissingEventId)?;

        let event_id = first_truthy_string(obj.get("source_event_id"))
            .or_else(|| first_truthy_string(obj.get("id")))
            .unwrap_or_default();
        if event_id.is_empty() {
            return Err(StoreError::MissingEventId);
        }

        let saved_at = truthy_f64(obj.get("saved_at")).unwrap_or(now_fallback);

        // Write the normalised fields back into the payload (store.py:58).
        obj.insert("saved_at".to_string(), Value::from(saved_at));
        obj.insert("source_event_id".to_string(), Value::from(event_id.clone()));

        let score = truthy_f64(obj.get("score"))
            .or_else(|| truthy_f64(obj.get("confidenceScore")))
            .unwrap_or(0.0);
        let label = first_truthy_string(obj.get("label")).unwrap_or_else(|| "unknown".to_string());

        let payload = serde_json::to_string(&result)?;

        let conn = self.conn.lock().expect("store mutex poisoned");
        conn.execute(
            "INSERT INTO triage_results (source_event_id, saved_at, score, label, payload_json)
             VALUES (?1, ?2, ?3, ?4, ?5)
             ON CONFLICT(source_event_id) DO UPDATE SET
                 saved_at=excluded.saved_at,
                 score=excluded.score,
                 label=excluded.label,
                 payload_json=excluded.payload_json",
            params![event_id, saved_at, score, label, payload],
        )?;
        Ok(result)
    }

    /// Fetch one stored payload by id (store.py:78-87).
    pub fn get(&self, source_event_id: &str) -> Result<Option<Value>> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let row: Option<String> = conn
            .query_row(
                "SELECT payload_json FROM triage_results WHERE source_event_id = ?1",
                params![source_event_id],
                |r| r.get(0),
            )
            .optional()?;
        match row {
            Some(s) => Ok(Some(serde_json::from_str(&s)?)),
            None => Ok(None),
        }
    }

    /// Most recent payloads, newest first (store.py:89-101). `limit` clamped to `[1, 500]`.
    pub fn recent(&self, limit: i64) -> Result<Vec<Value>> {
        let limit = limit.clamp(1, 500);
        let conn = self.conn.lock().expect("store mutex poisoned");
        let mut stmt = conn.prepare(
            "SELECT payload_json FROM triage_results ORDER BY saved_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |r| r.get::<_, String>(0))?;
        let mut out = Vec::new();
        for row in rows {
            out.push(serde_json::from_str(&row?)?);
        }
        Ok(out)
    }

    /// Total stored records (store.py:103-107).
    pub fn count(&self) -> Result<i64> {
        let conn = self.conn.lock().expect("store mutex poisoned");
        let n: i64 = conn.query_row("SELECT COUNT(*) FROM triage_results", [], |r| r.get(0))?;
        Ok(n)
    }

    /// Keyword-overlap search over persisted reason/action text (store.py:109-131).
    ///
    /// Pre-embeddings ranking: tokenise the query, pull a bounded recent window,
    /// score each candidate by the number of shared tokens, keep positives, and
    /// return the top `clamp(limit, 1, 50)` by overlap (ties keep recency order).
    pub fn search(&self, query_text: &str, limit: i64) -> Result<Vec<Value>> {
        let words = token_set(query_text);
        if words.is_empty() {
            return Ok(Vec::new());
        }

        let candidates = self.recent(200)?;
        let mut scored: Vec<(usize, Value)> = Vec::new();
        for item in candidates {
            let reason = text_field(&item, "reason", "reasoningExcerpt");
            let action = text_field(&item, "recommended_action", "recommendedAction");
            let blob = token_set(&format!("{reason} {action}"));
            let overlap = words.intersection(&blob).count();
            if overlap > 0 {
                scored.push((overlap, item));
            }
        }
        // Stable sort by descending overlap keeps recency order within ties,
        // matching Python's stable `list.sort(reverse=True)`.
        scored.sort_by_key(|(overlap, _)| std::cmp::Reverse(*overlap));
        let take = (limit.clamp(1, 50)) as usize;
        Ok(scored.into_iter().take(take).map(|(_, v)| v).collect())
    }
}

// ---------------------------------------------------------------------------
// Small Python-semantics helpers (kept local so the store has no dep on the
// scorer crate outside of tests).
// ---------------------------------------------------------------------------

/// `str(value)` if the value is truthy, else `None` — for `a or b` key chains.
fn first_truthy_string(v: Option<&Value>) -> Option<String> {
    match v {
        Some(Value::String(s)) if !s.is_empty() => Some(s.clone()),
        Some(Value::Number(n)) if n.as_f64().map(|f| f != 0.0).unwrap_or(false) => {
            Some(n.to_string())
        }
        Some(Value::Bool(true)) => Some("True".to_string()),
        _ => None,
    }
}

/// `float(value)` if the value is truthy and numeric, else `None`.
fn truthy_f64(v: Option<&Value>) -> Option<f64> {
    match v {
        Some(Value::Number(n)) => n.as_f64().filter(|f| *f != 0.0),
        Some(Value::String(s)) => s.trim().parse::<f64>().ok().filter(|f| *f != 0.0),
        _ => None,
    }
}

/// `str(item.get(a) or item.get(b) or "").lower()`.
fn text_field(item: &Value, a: &str, b: &str) -> String {
    let pick = item
        .get(a)
        .filter(|v| matches!(v, Value::String(s) if !s.is_empty()))
        .or_else(|| item.get(b));
    match pick {
        Some(Value::String(s)) => s.to_lowercase(),
        _ => String::new(),
    }
}

/// Tokenise like Python's `re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split()`:
/// lowercase, map every non-alphanumeric / non-whitespace byte to a space, then
/// split on ASCII whitespace into a unique set.
fn token_set(text: &str) -> std::collections::HashSet<String> {
    text.to_lowercase()
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c.is_whitespace() {
                c
            } else {
                ' '
            }
        })
        .collect::<String>()
        .split_whitespace()
        .map(|w| w.to_string())
        .collect()
}

// ===========================================================================
// Tests — ported from platform/ai-inference/test_triage.py (store cases).
// ===========================================================================
#[cfg(test)]
mod tests {
    use super::*;
    use nexus_triage::TriageModel;
    use serde_json::json;

    fn scored(model: &TriageModel, event: Value) -> Value {
        serde_json::to_value(model.triage_event(&event, 0.0)).unwrap()
    }

    #[test]
    fn list_recent_triage_store() {
        let dir = tempfile::tempdir().unwrap();
        let store = TriageStore::new(dir.path().join("t.db")).unwrap();
        let model = TriageModel::new();
        let event = json!({
            "id": "list-1", "dest_port": 443,
            "alert": {"severity": 2, "signature": "test", "category": "web-application-attack"}
        });
        store.upsert(scored(&model, event), 1.0).unwrap();
        let recent = store.recent(5).unwrap();
        assert!(recent
            .iter()
            .any(|r| r.get("source_event_id").and_then(|v| v.as_str()) == Some("list-1")));
    }

    #[test]
    fn store_upsert_get_search() {
        let dir = tempfile::tempdir().unwrap();
        let store = TriageStore::new(dir.path().join("t.db")).unwrap();
        let model = TriageModel::new();
        let mut result = scored(
            &model,
            json!({"id": "abc-123", "rule": {"id": 1, "level": 3, "description": "low noise"}}),
        );
        result["saved_at"] = json!(1.0);
        store.upsert(result, 0.0).unwrap();

        let got = store.get("abc-123").unwrap();
        assert!(got.is_some());
        assert_eq!(
            got.unwrap().get("source_event_id").and_then(|v| v.as_str()),
            Some("abc-123")
        );
        assert_eq!(store.count().unwrap(), 1);
        let hits = store.search("Wazuh level", 5).unwrap();
        assert!(!hits.is_empty());
    }

    #[test]
    fn upsert_without_event_id_errors() {
        let dir = tempfile::tempdir().unwrap();
        let store = TriageStore::new(dir.path().join("t.db")).unwrap();
        let err = store.upsert(json!({"score": 0.5}), 0.0);
        assert!(matches!(err, Err(StoreError::MissingEventId)));
    }
}
