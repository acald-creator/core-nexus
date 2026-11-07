//! NumPy-baseline triage scorer — Rust port of `platform/ai-inference/triage.py`.
//!
//! # Why this file exists
//!
//! The Python `triage.py` is the behavioural **oracle**. This crate reproduces
//! its scoring exactly so the SOC gateway and purple-eval tooling see identical
//! labels and scores whether the Python or Rust service is deployed. Every
//! non-obvious parity decision is called out in a `// PARITY:` comment. If you
//! change scoring here, change `triage.py` and both test suites in the same
//! commit, or the two will drift.
//!
//! # Model (unchanged from Python)
//!
//! A fixed linear scorer: extract a 5-feature vector from the event, take the
//! dot product with fixed weights, clamp to `[0, 1]`, then map the score to a
//! label. There is no training and no ML runtime — this is the Phase 1 baseline
//! (`docs/architecture/06-ai-soc-inference-engine.md` §1), not the Phase 3 ONNX
//! target.
//!
//! # Event shape
//!
//! Events arrive as arbitrary JSON objects (Suricata, Wazuh, or generic), so the
//! input type is [`serde_json::Value`] — the direct analogue of Python's
//! `dict[str, Any]`. The helper functions near the top of this file replicate
//! Python's loose `dict.get(...) or default` / truthiness semantics on that
//! dynamic value.

use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

// ===========================================================================
// Model constants (mirror TriageModel.__init__ in triage.py:40-48)
// ===========================================================================

/// Stable model identity reported in every result and on `/v1/models`.
pub const MODEL_NAME: &str = "nexus-triage-baseline";
/// Model version. Bumping this MUST change [`MODEL_DIGEST_INPUT`] too.
pub const MODEL_VERSION: &str = "1.1.0";
/// Exact bytes hashed to form the model digest (triage.py:44-46).
pub const MODEL_DIGEST_INPUT: &[u8] = b"nexus-triage-baseline-v1.1.0-weights-e2";
/// Expected SHA-256 of [`MODEL_DIGEST_INPUT`], locked against the Python output.
/// A unit test recomputes this so a typo in the input bytes fails the build.
pub const MODEL_DIGEST_HEX: &str =
    "cc993143cfb2775e3ebb2a40827e608c62456ea3686ab2a74f9943d9bd8ae432";
/// Decision threshold surfaced to clients (not used inside scoring).
pub const THRESHOLD: f64 = 0.65;
/// Linear weights for the 5 features. Order matches [`FEATURE_NAMES`].
pub const WEIGHTS: [f64; 5] = [0.35, 0.20, 0.20, 0.15, 0.10];

/// Feature names, in weight order (triage.py:31-37).
pub const FEATURE_NAMES: [&str; 5] = [
    "severity",
    "port_or_rule_risk",
    "signature_or_text_risk",
    "category_or_groups",
    "athena_context",
];

/// Header/field keys that carry an explicit Athena **scenario id** (triage.py:11-16).
pub const ATHENA_SCENARIO_ID_KEYS: [&str; 4] = [
    "X-Athena-Scenario-Id",
    "x-athena-scenario-id",
    "scenario_id",
    "scenarioId",
];
/// Header/field keys that carry a human-readable Athena **label** (triage.py:18-23).
pub const ATHENA_LABEL_KEYS: [&str; 4] = [
    "X-Athena-Scenario",
    "x-athena-scenario",
    "athena_scenario",
    "athenaScenario",
];

/// Suricata `dest_port` values treated as high risk (triage.py:144).
const HIGH_RISK_PORTS: [i64; 8] = [22, 23, 445, 3389, 139, 5900, 2375, 10250];
/// Signature keywords that flag a Suricata alert as malicious (triage.py:149-159).
const SURICATA_KEYWORDS: [&str; 9] = [
    "exploit", "cve", "shellcode", "reverse", "malware", "scan", "bruteforce",
    "trojan", "ransomware",
];
/// Suricata categories treated as high risk (triage.py:163-170).
const SURICATA_CATEGORIES: [&str; 6] = [
    "attempted-admin",
    "attempted-user",
    "policy-violation",
    "shellcode-detect",
    "trojan-activity",
    "web-application-attack",
];
/// Wazuh rule ids treated as high severity (triage.py:212).
const WAZUH_HIGH_RISK_RULES: [i64; 6] = [5710, 5712, 5716, 5720, 5503, 18107];
/// Wazuh description keywords that indicate risk (triage.py:220-230).
const WAZUH_KEYWORDS: [&str; 9] = [
    "failed", "attack", "unauthorized", "shell", "privilege", "root", "cve",
    "exploit", "malware",
];
/// Substring tokens that make a Wazuh group high risk (triage.py:238-247).
const WAZUH_GROUP_TOKENS: [&str; 8] = [
    "authentication_failed",
    "exploit_attempt",
    "attack",
    "rootcheck",
    "virus",
    "web",
    "ids",
    "pci_dss",
];

// ===========================================================================
// Python-semantics helpers on serde_json::Value
//
// These exist so the extractors below can read like the Python line-for-line.
// Python's `d.get(k)` returns None for a missing key, and `if d.get(k):` tests
// truthiness (None/0/""/[]/{}/False are falsy). We replicate exactly that.
// ===========================================================================

/// Python truthiness for a JSON value (`None`/`0`/`""`/`[]`/`{}`/`false` are falsy).
fn truthy(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_f64().map(|f| f != 0.0).unwrap_or(false),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

/// `str(value)` for the value kinds Athena/MITRE fields actually carry
/// (strings and numbers). Booleans use Python's `True`/`False` spelling; other
/// kinds fall back to compact JSON, which the Python code never reaches here.
fn stringify(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        Value::Bool(b) => if *b { "True" } else { "False" }.to_string(),
        Value::Null => "None".to_string(),
        other => other.to_string(),
    }
}

/// `obj.get(key)` — `None` unless `obj` is an object that has `key`.
fn get<'a>(obj: &'a Value, key: &str) -> Option<&'a Value> {
    obj.as_object().and_then(|m| m.get(key))
}

/// `obj.get(key)` filtered to truthy values — the common `if obj.get(key):` form.
fn get_truthy<'a>(obj: &'a Value, key: &str) -> Option<&'a Value> {
    get(obj, key).filter(|v| truthy(v))
}

/// First key whose value is truthy, stringified — the `a or b or c` chains.
fn first_truthy_str(obj: &Value, keys: &[&str]) -> Option<String> {
    keys.iter().find_map(|k| get_truthy(obj, k).map(stringify))
}

/// `int(obj.get(key, default) or default)` — truthy-or-default, then to i64.
///
/// PARITY: this helper is LENIENT for every caller — a non-numeric string (or a
/// float string like `"2.5"`) falls back to `default`. Python only wraps
/// `rule.id` in try/except (triage.py:213-215); for `severity`, `dest_port`, and
/// `level` Python calls a bare `int()`, which RAISES on a non-numeric string and
/// surfaces as an HTTP 500. We deliberately do NOT reproduce that crash — bad
/// input is scored leniently instead. See PARITY.md "Known divergences".
fn get_int_or(obj: &Value, key: &str, default: i64) -> i64 {
    match get(obj, key) {
        Some(v) if truthy(v) => as_i64(v).unwrap_or(default),
        _ => default,
    }
}

/// Best-effort `int(value)` — truncates floats toward zero, parses numeric strings.
fn as_i64(v: &Value) -> Option<i64> {
    match v {
        Value::Number(n) => n.as_i64().or_else(|| n.as_f64().map(|f| f as i64)),
        Value::String(s) => s
            .trim()
            .parse::<i64>()
            .ok()
            .or_else(|| s.trim().parse::<f64>().ok().map(|f| f as i64)),
        _ => None,
    }
}

/// `data.get("headers") or data.get("http_headers")`, preferring a truthy value.
fn pick_headers(data: &Value) -> Option<&Value> {
    get_truthy(data, "headers").or_else(|| get_truthy(data, "http_headers"))
}

/// Case-insensitive header lookup over an object (`{k.lower(): v}` then `.get`).
///
/// PARITY: Python builds a lowercased dict so a later duplicate wins; we return
/// the last match to match that, which is irrelevant unless a payload carries
/// two headers differing only in case.
fn header_ci<'a>(headers: &'a Value, lower_key: &str) -> Option<&'a Value> {
    let obj = headers.as_object()?;
    obj.iter()
        .filter(|(k, _)| k.to_lowercase() == lower_key)
        .map(|(_, v)| v)
        .next_back()
}

/// Wrap an optional string as a JSON value (`Some(s)` -> string, `None` -> null).
fn jopt(o: Option<String>) -> Value {
    o.map(Value::String).unwrap_or(Value::Null)
}

/// Read a top-level string field back out of the built `meta` object.
fn meta_str(meta: &Value, key: &str) -> Option<String> {
    get(meta, key).and_then(|v| v.as_str()).map(str::to_string)
}

/// Round to 4 decimals using banker's rounding, matching Python's `round(x, 4)`.
///
/// PARITY: Python's `round` is round-half-to-even. Test scores never land on an
/// exact 4-decimal half, so this only matters for byte-identical output.
fn round4(x: f64) -> f64 {
    let scaled = x * 10_000.0;
    let floor = scaled.floor();
    let diff = scaled - floor;
    // Round up on a strict excess, or on an exact half only when the floor is
    // odd (round-half-to-even); otherwise round down.
    let rounded = if diff > 0.5 || (diff == 0.5 && (floor as i64) % 2 != 0) {
        floor + 1.0
    } else {
        floor
    };
    rounded / 10_000.0
}

// ===========================================================================
// Public types
// ===========================================================================

/// Which event family produced the features. Serializes to the exact strings
/// `"Suricata"`, `"Wazuh"`, `"Generic"` used by the Python `event_type`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum EventType {
    Suricata,
    Wazuh,
    Generic,
}

impl std::fmt::Display for EventType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            EventType::Suricata => "Suricata",
            EventType::Wazuh => "Wazuh",
            EventType::Generic => "Generic",
        };
        f.write_str(s)
    }
}

/// The 5-feature vector. Field order matches [`FEATURE_NAMES`] / [`WEIGHTS`].
#[derive(Debug, Clone, Copy, PartialEq)]
struct Features {
    severity: f64,
    port_or_rule_risk: f64,
    signature_or_text_risk: f64,
    category_or_groups: f64,
    athena_context: f64,
}

impl Features {
    /// Generic/unknown event vector (triage.py:314).
    const GENERIC: Features = Features {
        severity: 0.1,
        port_or_rule_risk: 0.1,
        signature_or_text_risk: 0.1,
        category_or_groups: 0.0,
        athena_context: 0.0,
    };

    /// Dot product with the model weights (`np.dot(features, weights)`).
    fn dot(&self, w: &[f64; 5]) -> f64 {
        self.severity * w[0]
            + self.port_or_rule_risk * w[1]
            + self.signature_or_text_risk * w[2]
            + self.category_or_groups * w[3]
            + self.athena_context * w[4]
    }

    /// Rounded `features_used` map emitted in the result.
    fn rounded(&self) -> FeaturesUsed {
        FeaturesUsed {
            severity: round4(self.severity),
            port_or_rule_risk: round4(self.port_or_rule_risk),
            signature_or_text_risk: round4(self.signature_or_text_risk),
            category_or_groups: round4(self.category_or_groups),
            athena_context: round4(self.athena_context),
        }
    }
}

/// Rounded per-feature values echoed back in the result (`features_used`).
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct FeaturesUsed {
    pub severity: f64,
    pub port_or_rule_risk: f64,
    pub signature_or_text_risk: f64,
    pub category_or_groups: f64,
    pub athena_context: f64,
}

/// A fully scored triage result.
///
/// Field order and the snake_case/camelCase duplicates mirror the Python dict
/// returned by `triage_event` (triage.py:355-378) exactly. The camelCase
/// aliases (`confidenceScore`, `reasoningExcerpt`, `recommendedAction`) exist
/// for the Nexus Console; do not remove them.
#[derive(Debug, Clone, Serialize)]
pub struct TriageResult {
    pub source_event_id: String,
    pub timestamp: String,
    pub model_name: String,
    pub model_version: String,
    pub model_digest: String,
    pub score: f64,
    #[serde(rename = "confidenceScore")]
    pub confidence_score: f64,
    pub label: String,
    pub threshold: f64,
    pub reason: String,
    #[serde(rename = "reasoningExcerpt")]
    pub reasoning_excerpt: String,
    pub features_used: FeaturesUsed,
    pub recommended_action: String,
    #[serde(rename = "recommendedAction")]
    pub recommended_action_camel: String,
    pub event_type: EventType,
    pub athena_scenario: Option<String>,
    pub scenario_id: Option<String>,
    pub technique: Option<String>,
    pub feature_meta: Value,
}

/// The fixed linear triage model. Stateless and cheap to clone.
#[derive(Debug, Clone)]
pub struct TriageModel {
    pub model_name: String,
    pub model_version: String,
    pub model_digest: String,
    pub threshold: f64,
    pub weights: [f64; 5],
}

impl Default for TriageModel {
    fn default() -> Self {
        Self::new()
    }
}

impl TriageModel {
    /// Build the model, computing the digest from [`MODEL_DIGEST_INPUT`].
    pub fn new() -> Self {
        let mut hasher = Sha256::new();
        hasher.update(MODEL_DIGEST_INPUT);
        let digest = hex::encode(hasher.finalize());
        TriageModel {
            model_name: MODEL_NAME.to_string(),
            model_version: MODEL_VERSION.to_string(),
            model_digest: digest,
            threshold: THRESHOLD,
            weights: WEIGHTS,
        }
    }

    /// Score a single event. `now_fallback` is the Unix time used for the
    /// `timestamp` field only when the event carries none — injected so tests
    /// are deterministic (the Python code calls `time.time()` inline).
    pub fn triage_event(&self, event: &Value, now_fallback: f64) -> TriageResult {
        // Identity + timestamp (triage.py:296-305).
        let event_id = first_truthy_str(event, &["event_id", "id", "_id", "alert_id"])
            .unwrap_or_else(|| "unknown-event-id".to_string());
        let timestamp = first_truthy_str(event, &["timestamp", "date", "@timestamp"])
            .unwrap_or_else(|| format!("{now_fallback}"));

        // Event-family routing (triage.py:307-321).
        let is_suricata = get(event, "alert").map(|v| v.is_object()).unwrap_or(false)
            || event.as_object().map(|m| m.contains_key("dest_port")).unwrap_or(false);
        let is_wazuh = get(event, "rule")
            .map(|v| v.is_object() || truthy(v))
            .unwrap_or(false);

        let (features, explanation, meta, event_type) = if is_suricata {
            let (f, e, m) = self.suricata_features(event);
            (f, e, m, EventType::Suricata)
        } else if is_wazuh {
            let (f, e, m) = self.wazuh_features(event);
            (f, e, m, EventType::Wazuh)
        } else {
            let meta = json!({
                "athena_scenario": jopt(extract_athena_scenario(event)),
                "scenario_id": jopt(extract_scenario_id(event)),
                "technique": jopt(extract_technique(event)),
            });
            (
                Features::GENERIC,
                vec!["Generic/unknown event format".to_string()],
                meta,
                EventType::Generic,
            )
        };

        // Score: clamp(dot, 0, 1) on the UNROUNDED value (triage.py:323).
        let raw_score = features.dot(&self.weights).clamp(0.0, 1.0);

        let athena_scenario = meta_str(&meta, "athena_scenario");
        let (label, recommended_action) = classify(raw_score, athena_scenario.as_deref());

        // Reason string (triage.py:352-353).
        let reason_body = if explanation.is_empty() {
            "No anomalies detected.".to_string()
        } else {
            explanation.join(" | ")
        };
        let reason = format!("[{event_type}] {reason_body}");

        let rounded = round4(raw_score);
        TriageResult {
            source_event_id: event_id,
            timestamp,
            model_name: self.model_name.clone(),
            model_version: self.model_version.clone(),
            model_digest: self.model_digest.clone(),
            score: rounded,
            confidence_score: rounded,
            label,
            threshold: self.threshold,
            reason: reason.clone(),
            reasoning_excerpt: reason,
            features_used: features.rounded(),
            recommended_action: recommended_action.clone(),
            recommended_action_camel: recommended_action,
            event_type,
            athena_scenario,
            scenario_id: meta_str(&meta, "scenario_id"),
            technique: meta_str(&meta, "technique"),
            feature_meta: meta,
        }
    }

    /// Suricata feature pack (port of `_extract_suricata_features`, triage.py:128-203).
    fn suricata_features(&self, event: &Value) -> (Features, Vec<String>, Value) {
        let alert = get(event, "alert").filter(|v| v.is_object());
        let alert_nonempty = alert
            .and_then(|a| a.as_object())
            .map(|o| !o.is_empty())
            .unwrap_or(false);

        let severity = alert.map(|a| get_int_or(a, "severity", 3)).unwrap_or(3);
        // PARITY: severity_score keys off whether the alert object is non-empty.
        let severity_score = if alert_nonempty {
            match severity {
                1 => 1.0,
                2 => 0.6,
                _ => 0.3,
            }
        } else {
            0.1
        };

        let dest_port = get_int_or(event, "dest_port", 0);
        let port_score = if HIGH_RISK_PORTS.contains(&dest_port) {
            1.0
        } else if dest_port > 0 {
            0.3
        } else {
            0.0
        };

        let sig = alert
            .and_then(|a| get_truthy(a, "signature"))
            .map(stringify)
            .unwrap_or_default()
            .to_lowercase();
        let category = alert
            .and_then(|a| get_truthy(a, "category"))
            .map(stringify)
            .unwrap_or_default()
            .to_lowercase();

        let keyword_match = SURICATA_KEYWORDS.iter().any(|kw| sig.contains(kw));
        let sig_score = if keyword_match {
            1.0
        } else if !sig.is_empty() {
            0.2
        } else {
            0.0
        };

        let cat_score = if SURICATA_CATEGORIES.contains(&category.as_str()) {
            1.0
        } else if !category.is_empty() {
            0.4
        } else {
            0.0
        };

        let scenario = extract_athena_scenario(event);
        let scenario_id = extract_scenario_id(event);
        let technique = extract_technique(event);
        let (athena_score, athena_explain) = athena_feature(scenario.as_deref());

        let mut explanation: Vec<String> = Vec::new();
        if alert_nonempty {
            explanation.push(format!("Suricata alert severity {severity}"));
        }
        if HIGH_RISK_PORTS.contains(&dest_port) {
            explanation.push(format!("Targeting high-risk port {dest_port}"));
        }
        if keyword_match {
            explanation.push("Malicious signature keywords detected".to_string());
        }
        if !category.is_empty() {
            explanation.push(format!("Suricata category '{category}'"));
        }
        explanation.extend(athena_explain);

        // Raw (unlowercased) signature + flexible-typed ids are preserved in meta.
        let sig_raw = alert
            .and_then(|a| get(a, "signature"))
            .cloned()
            .unwrap_or(Value::Null);
        // PARITY: Python `alert.get("signature_id") or alert.get("sid")` returns
        // the RAW `sid` value whenever `signature_id` is falsy — even if `sid` is
        // itself falsy (e.g. `0`). So only `signature_id` is truthy-filtered; the
        // `sid` fallback is taken verbatim.
        let sig_id = match alert.and_then(|a| get_truthy(a, "signature_id")) {
            Some(v) => v.clone(),
            None => alert.and_then(|a| get(a, "sid")).cloned().unwrap_or(Value::Null),
        };
        let app_proto = get(event, "app_proto").cloned().unwrap_or(Value::Null);

        let meta = json!({
            "suricata_category": if category.is_empty() { Value::Null } else { Value::String(category) },
            "suricata_signature": sig_raw,
            "suricata_signature_id": sig_id,
            "dest_port": if dest_port != 0 { Value::from(dest_port) } else { Value::Null },
            "app_proto": app_proto,
            "athena_scenario": jopt(scenario),
            "scenario_id": jopt(scenario_id),
            "technique": jopt(technique),
        });

        let features = Features {
            severity: severity_score,
            port_or_rule_risk: port_score,
            signature_or_text_risk: sig_score,
            category_or_groups: cat_score,
            athena_context: athena_score,
        };
        (features, explanation, meta)
    }

    /// Wazuh feature pack (port of `_extract_wazuh_features`, triage.py:205-293).
    fn wazuh_features(&self, event: &Value) -> (Features, Vec<String>, Value) {
        let rule = get(event, "rule").filter(|v| v.is_object());

        let level = rule.map(|r| get_int_or(r, "level", 0)).unwrap_or(0);
        let severity_score = (level as f64 / 15.0).min(1.0);

        let rule_id = rule.map(|r| get_int_or(r, "id", 0)).unwrap_or(0);
        let rule_score = if WAZUH_HIGH_RISK_RULES.contains(&rule_id) {
            1.0
        } else if level >= 7 {
            0.5
        } else {
            0.1
        };

        let desc = rule
            .and_then(|r| get_truthy(r, "description"))
            .map(stringify)
            .unwrap_or_default()
            .to_lowercase();
        let keyword_match = WAZUH_KEYWORDS.iter().any(|kw| desc.contains(kw));
        let desc_score = if keyword_match {
            1.0
        } else if !desc.is_empty() {
            0.2
        } else {
            0.0
        };

        // groups: normalise to a lowercased Vec<String> (triage.py:234-237).
        let groups_l: Vec<String> = match rule.and_then(|r| get(r, "groups")) {
            Some(Value::Array(a)) => a.iter().map(|g| stringify(g).to_lowercase()).collect(),
            Some(v) if truthy(v) => vec![stringify(v).to_lowercase()],
            _ => Vec::new(),
        };
        let group_hit = groups_l
            .iter()
            .any(|g| WAZUH_GROUP_TOKENS.iter().any(|tok| g.contains(tok)));

        // MITRE ids from rule.mitre.{id,technique,tactic} (triage.py:252-260).
        // PARITY: the list branch keeps ALL items (no truthy filter), unlike the
        // recursive _collect_mitre_ids helper used elsewhere.
        let mut mitre_ids: Vec<String> = Vec::new();
        if let Some(m) = rule.and_then(|r| get(r, "mitre")).filter(|v| v.is_object()) {
            for key in ["id", "technique", "tactic"] {
                match get(m, key) {
                    Some(Value::Array(a)) => mitre_ids.extend(a.iter().map(stringify)),
                    Some(v) if truthy(v) => mitre_ids.push(stringify(v)),
                    _ => {}
                }
            }
        }
        let mitre_score = if mitre_ids.is_empty() { 0.0 } else { 0.8 };
        let groups_score = f64::max(
            if group_hit { 1.0 } else { 0.0 },
            f64::max(mitre_score, if groups_l.is_empty() { 0.0 } else { 0.3 }),
        );

        let scenario = extract_athena_scenario(event);
        let scenario_id = extract_scenario_id(event);
        let technique = extract_technique(event).or_else(|| mitre_ids.first().cloned());
        let (athena_score, athena_explain) = athena_feature(scenario.as_deref());

        let mut explanation: Vec<String> = Vec::new();
        if level > 0 {
            explanation.push(format!("Wazuh alert level {level}"));
        }
        if WAZUH_HIGH_RISK_RULES.contains(&rule_id) {
            explanation.push(format!("Wazuh high-severity rule ID {rule_id}"));
        }
        if keyword_match {
            explanation.push("Alert description contains security risk indicators".to_string());
        }
        if group_hit {
            explanation.push(format!(
                "Wazuh groups indicate risk ({})",
                join_first(&groups_l, 4)
            ));
        }
        if !mitre_ids.is_empty() {
            explanation.push(format!("MITRE refs: {}", join_first(&mitre_ids, 4)));
        }
        explanation.extend(athena_explain);

        let meta = json!({
            "wazuh_rule_id": if rule_id != 0 { Value::from(rule_id) } else { Value::Null },
            "wazuh_groups": groups_l,
            "mitre": mitre_ids,
            "athena_scenario": jopt(scenario),
            "scenario_id": jopt(scenario_id),
            "technique": jopt(technique),
        });

        let features = Features {
            severity: severity_score,
            port_or_rule_risk: rule_score,
            signature_or_text_risk: desc_score,
            category_or_groups: groups_score,
            athena_context: athena_score,
        };
        (features, explanation, meta)
    }
}

// ===========================================================================
// Free functions shared by both feature packs
// ===========================================================================

/// `', '.join(items[:n])`.
fn join_first(items: &[String], n: usize) -> String {
    items.iter().take(n).cloned().collect::<Vec<_>>().join(", ")
}

/// Athena-label feature (triage.py:121-126). Labeled training/stimulation
/// traffic is boosted for review, never auto-contained.
fn athena_feature(scenario: Option<&str>) -> (f64, Vec<String>) {
    match scenario {
        Some(s) => (0.7, vec![format!("Athena scenario label present ({s})")]),
        None => (0.0, Vec::new()),
    }
}

/// Port of `_extract_athena_scenario` (triage.py:50-68).
fn extract_athena_scenario(event: &Value) -> Option<String> {
    let all_keys = ATHENA_SCENARIO_ID_KEYS.iter().chain(ATHENA_LABEL_KEYS.iter());
    for k in all_keys.clone() {
        if let Some(v) = get_truthy(event, k) {
            return Some(stringify(v));
        }
    }
    let data = get(event, "data").filter(|v| v.is_object())?;
    for k in all_keys {
        if let Some(v) = get_truthy(data, k) {
            return Some(stringify(v));
        }
    }
    let headers = pick_headers(data)?;
    for lk in ["x-athena-scenario", "x-athena-scenario-id", "x-athena-label"] {
        if let Some(v) = header_ci(headers, lk).filter(|v| truthy(v)) {
            return Some(stringify(v));
        }
    }
    None
}

/// Port of `_extract_scenario_id` (triage.py:70-88): prefer an explicit id,
/// fall back to a label, then to [`extract_athena_scenario`].
fn extract_scenario_id(event: &Value) -> Option<String> {
    for k in ATHENA_SCENARIO_ID_KEYS {
        if let Some(v) = get_truthy(event, k) {
            return Some(stringify(v));
        }
    }
    if let Some(data) = get(event, "data").filter(|v| v.is_object()) {
        for k in ATHENA_SCENARIO_ID_KEYS {
            if let Some(v) = get_truthy(data, k) {
                return Some(stringify(v));
            }
        }
        if let Some(headers) = pick_headers(data) {
            if let Some(v) = header_ci(headers, "x-athena-scenario-id").filter(|v| truthy(v)) {
                return Some(stringify(v));
            }
        }
    }
    for k in ATHENA_LABEL_KEYS {
        if let Some(v) = get_truthy(event, k) {
            return Some(stringify(v));
        }
    }
    extract_athena_scenario(event)
}

/// Port of `_collect_mitre_ids` (triage.py:90-102). Recurses through lists;
/// filters falsy list items (unlike the inline Wazuh collector).
fn collect_mitre_ids(raw: Option<&Value>) -> Vec<String> {
    let mut ids = Vec::new();
    match raw {
        Some(Value::Object(_)) => {
            let obj = raw.unwrap();
            for key in ["id", "technique", "tactic"] {
                match get(obj, key) {
                    Some(Value::Array(a)) => {
                        ids.extend(a.iter().filter(|x| truthy(x)).map(stringify))
                    }
                    Some(v) if truthy(v) => ids.push(stringify(v)),
                    _ => {}
                }
            }
        }
        Some(Value::Array(a)) => {
            for item in a {
                ids.extend(collect_mitre_ids(Some(item)));
            }
        }
        _ => {}
    }
    ids
}

/// Port of `_extract_technique` (triage.py:104-119).
fn extract_technique(event: &Value) -> Option<String> {
    if let Some(v) = get_truthy(event, "technique") {
        return Some(stringify(v));
    }
    let alert = get(event, "alert").filter(|v| v.is_object());
    let ids = collect_mitre_ids(alert.and_then(|a| get(a, "mitre")));
    if let Some(first) = ids.first() {
        return Some(first.clone());
    }
    let rule = get(event, "rule").filter(|v| v.is_object());
    let ids = collect_mitre_ids(rule.and_then(|r| get(r, "mitre")));
    if let Some(first) = ids.first() {
        return Some(first.clone());
    }
    let data = get(event, "data").filter(|v| v.is_object())?;
    get_truthy(data, "technique").map(stringify)
}

/// Map a clamped score (+ Athena presence) to a label and recommended action
/// (triage.py:325-350). PARITY: the `needs_human_review` band is entered when
/// the score is below 0.75 **or** the traffic is Athena-labeled, so labeled
/// high-score traffic is reviewed rather than auto-contained.
fn classify(score: f64, athena_scenario: Option<&str>) -> (String, String) {
    if score < 0.3 {
        (
            "benign".to_string(),
            "Allow traffic and monitor logs.".to_string(),
        )
    } else if score < 0.6 {
        (
            "suspicious".to_string(),
            "Increase telemetry logging frequency and alert on subsequent events.".to_string(),
        )
    } else if score < 0.75 || athena_scenario.is_some() {
        let mut action =
            "Expose threat context to analyst workbench for manual inspection.".to_string();
        if let Some(s) = athena_scenario {
            action.push_str(&format!(
                " Athena-labeled traffic ({s}) — treat as stimulation/emulation until verified."
            ));
        }
        ("needs_human_review".to_string(), action)
    } else {
        (
            "likely_true_positive".to_string(),
            "Draft containment policy for human approval: isolate source workload \
             using a Kubernetes NetworkPolicy (do not auto-apply)."
                .to_string(),
        )
    }
}

// ===========================================================================
// Oracle tests — ported 1:1 from platform/ai-inference/test_triage.py
//
// Keep these in lockstep with the Python suite. A new Python case => a new case
// here. The two numeric parity tests additionally pin exact scores so a silent
// arithmetic drift fails.
// ===========================================================================
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn model() -> TriageModel {
        TriageModel::new()
    }

    #[test]
    fn digest_matches_python() {
        assert_eq!(model().model_digest, MODEL_DIGEST_HEX);
    }

    #[test]
    fn suricata_category_and_athena_review() {
        let r = model().triage_event(
            &json!({
                "id": "suri-1",
                "dest_port": 445,
                "alert": {
                    "severity": 1,
                    "signature": "ET EXPLOIT Possible SMB scan",
                    "category": "trojan-activity"
                },
                "X-Athena-Scenario": "juice-shop-day11"
            }),
            0.0,
        );
        assert_eq!(r.event_type, EventType::Suricata);
        assert_eq!(r.confidence_score, r.score);
        assert_eq!(r.recommended_action_camel, r.recommended_action);
        assert_eq!(r.athena_scenario.as_deref(), Some("juice-shop-day11"));
        assert_eq!(r.label, "needs_human_review");
        let action = r.recommended_action.to_lowercase();
        assert!(action.contains("human") || action.contains("analyst"));
        assert!(!action.contains("containment") || action.contains("approval"));
    }

    #[test]
    fn athena_scenario_id_header_review() {
        let r = model().triage_event(
            &json!({
                "id": "suri-2",
                "dest_port": 8090,
                "technique": "T1046",
                "alert": {
                    "severity": 1,
                    "signature": "GET /api/v1/novels",
                    "category": "trojan-activity"
                },
                "X-Athena-Scenario-Id": "night-quire-recon-run"
            }),
            0.0,
        );
        assert_eq!(r.athena_scenario.as_deref(), Some("night-quire-recon-run"));
        assert_eq!(r.scenario_id.as_deref(), Some("night-quire-recon-run"));
        assert_eq!(r.technique.as_deref(), Some("T1046"));
        assert_eq!(r.label, "needs_human_review");
    }

    #[test]
    fn athena_scenario_label_header_review() {
        let r = model().triage_event(
            &json!({
                "id": "suri-3",
                "dest_port": 8090,
                "alert": {
                    "severity": 1,
                    "signature": "ET SCAN probe",
                    "category": "trojan-activity"
                },
                "X-Athena-Scenario": "night-quire"
            }),
            0.0,
        );
        assert_eq!(r.athena_scenario.as_deref(), Some("night-quire"));
        assert_eq!(r.label, "needs_human_review");
    }

    #[test]
    fn wazuh_groups_and_mitre() {
        let r = model().triage_event(
            &json!({
                "id": "wazuh-9",
                "rule": {
                    "id": 5710,
                    "level": 10,
                    "description": "sshd: authentication failed",
                    "groups": ["authentication_failed", "sshd"],
                    "mitre": {"id": ["T1110"]}
                }
            }),
            0.0,
        );
        assert_eq!(r.event_type, EventType::Wazuh);
        assert!(r.score >= 0.6);
        assert!(r.reason.to_lowercase().contains("mitre"));
        assert!(r.features_used.category_or_groups > 0.0);
    }

    #[test]
    fn high_score_without_athena_requests_human_approved_containment() {
        let r = model().triage_event(
            &json!({
                "id": "suri-hot",
                "dest_port": 445,
                "alert": {
                    "severity": 1,
                    "signature": "ET EXPLOIT reverse shellcode ransomware",
                    "category": "shellcode-detect"
                }
            }),
            0.0,
        );
        assert_eq!(r.athena_scenario, None);
        assert_eq!(r.label, "likely_true_positive");
        assert!(r.recommended_action.to_lowercase().contains("human approval"));
    }

    // --- numeric parity anchors (not in the Python suite; lock exact scores) ---

    #[test]
    fn parity_suricata_score_exact() {
        // features [1.0, 1.0, 1.0, 1.0, 0.7] . weights = 0.97
        let r = model().triage_event(
            &json!({
                "id": "p1", "dest_port": 445,
                "alert": {"severity": 1, "signature": "ET EXPLOIT scan", "category": "trojan-activity"},
                "X-Athena-Scenario": "s"
            }),
            0.0,
        );
        assert_eq!(r.score, 0.97);
    }

    #[test]
    fn parity_wazuh_score_exact() {
        // features [0.6667, 1.0, 1.0, 1.0, 0.0] . weights = 0.78333..
        let r = model().triage_event(
            &json!({
                "id": "p2",
                "rule": {"id": 5710, "level": 10, "description": "authentication failed",
                         "groups": ["authentication_failed"], "mitre": {"id": ["T1110"]}}
            }),
            0.0,
        );
        assert_eq!(r.score, 0.7833);
        assert_eq!(r.features_used.severity, 0.6667);
    }

    #[test]
    fn signature_id_or_sid_fallback_matches_python() {
        // Python `signature_id or sid`: when signature_id is falsy (0), the raw
        // `sid` value (77) is kept. Regression lock for review finding 10.
        let r = model().triage_event(
            &json!({
                "id": "x", "dest_port": 445,
                "alert": {"severity": 1, "signature": "s", "category": "trojan-activity",
                          "signature_id": 0, "sid": 77}
            }),
            0.0,
        );
        assert_eq!(r.feature_meta["suricata_signature_id"], json!(77));
    }

    #[test]
    fn generic_event_is_benign() {
        let r = model().triage_event(&json!({"id": "g1", "foo": "bar"}), 0.0);
        assert_eq!(r.event_type, EventType::Generic);
        assert_eq!(r.label, "benign");
    }
}
