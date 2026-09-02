"""Pure alert transform/filter helpers (property-testable)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.models.alerts import SOCAlert

SEVERITY_ORDER = ("critical", "high", "medium", "low", "informational")
ATHENA_SCENARIO_KEYS = (
    "X-Athena-Scenario",
    "x-athena-scenario",
    "X-Athena-Scenario-Id",
    "x-athena-scenario-id",
    "athena_scenario",
    "athenaScenario",
)


def clamp_limit(limit: int | None) -> int:
    """Clamp limit to [1, 500]; default 100 when absent."""
    if limit is None:
        return 100
    return max(1, min(500, int(limit)))


def map_athena_scenario(raw: dict[str, Any]) -> str | None:
    """Extract Athena scenario label from Wazuh alert metadata, if present."""
    for key in ATHENA_SCENARIO_KEYS:
        if key in raw and raw[key]:
            return str(raw[key])

    data = raw.get("data")
    if isinstance(data, dict):
        for key in ATHENA_SCENARIO_KEYS:
            if key in data and data[key]:
                return str(data[key])
        headers = data.get("headers") or data.get("http_headers")
        if isinstance(headers, dict):
            for key in ATHENA_SCENARIO_KEYS:
                if key in headers and headers[key]:
                    return str(headers[key])
            # Case-insensitive header lookup
            lowered = {str(k).lower(): v for k, v in headers.items()}
            if "x-athena-scenario" in lowered and lowered["x-athena-scenario"]:
                return str(lowered["x-athena-scenario"])
            if "x-athena-scenario-id" in lowered and lowered["x-athena-scenario-id"]:
                return str(lowered["x-athena-scenario-id"])

    decoder = raw.get("decoder")
    if isinstance(decoder, dict) and decoder.get("name") == "athena":
        # Fall through — still prefer explicit header fields above
        pass

    return None


def _level_to_severity(level: int) -> str:
    if level >= 15:
        return "critical"
    if level >= 12:
        return "high"
    if level >= 7:
        return "medium"
    if level >= 4:
        return "low"
    return "informational"


ALERT_SOURCES = frozenset(
    {"wazuh", "suricata", "zeek", "falco", "tetragon", "ai-inference", "vector"}
)


def _detect_source(raw: dict[str, Any]) -> str:
    explicit = str(raw.get("source") or raw.get("nexus.source") or "").lower()
    if explicit in ALERT_SOURCES:
        return explicit

    rule = raw.get("rule") if isinstance(raw.get("rule"), dict) else {}
    groups = rule.get("groups") or []
    groups_l = [str(g).lower() for g in groups] if isinstance(groups, list) else []
    if any("suricata" in g for g in groups_l):
        return "suricata"
    if any("zeek" in g for g in groups_l):
        return "zeek"
    if any("falco" in g for g in groups_l):
        return "falco"
    if any("tetragon" in g for g in groups_l):
        return "tetragon"

    decoder = raw.get("decoder")
    if isinstance(decoder, dict):
        name = str(decoder.get("name", "")).lower()
        if "suricata" in name:
            return "suricata"
        if "zeek" in name:
            return "zeek"
    return "wazuh"


def _triage_source(record: dict[str, Any], meta: dict[str, Any], event_type: str) -> str:
    for key in ("nexus.source", "source", "sensor"):
        val = record.get(key) or meta.get(key)
        if val and str(val).lower() in ALERT_SOURCES:
            return str(val).lower()
    et = event_type.lower()
    if et in ALERT_SOURCES:
        return et
    if et == "suricata":
        return "suricata"
    if et in {"wazuh", "generic"}:
        # Generic triage without sensor tag → AI inference store
        return "ai-inference" if et == "generic" else "wazuh"
    return "ai-inference"


def _score_to_severity(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.7:
        return "high"
    if score >= 0.5:
        return "medium"
    if score >= 0.3:
        return "low"
    return "informational"


def map_triage_alert(record: dict[str, Any]) -> SOCAlert:
    """Map a persisted ai-inference triage record to SOCAlert (ADR 0011 H2)."""
    meta = record.get("feature_meta") if isinstance(record.get("feature_meta"), dict) else {}
    score = float(record.get("score") or record.get("confidenceScore") or 0.0)
    event_type = str(record.get("event_type") or "Generic")
    source = _triage_source(record, meta, event_type)

    rule_name = str(
        record.get("reason")
        or record.get("reasoningExcerpt")
        or meta.get("suricata_signature")
        or f"AI triage ({record.get('label') or 'unknown'})"
    )
    affected_host = str(
        meta.get("affected_host")
        or meta.get("host")
        or (f"port-{meta['dest_port']}" if meta.get("dest_port") else "unknown")
    )
    scenario = (
        record.get("athena_scenario")
        or record.get("scenario_id")
        or meta.get("athena_scenario")
        or meta.get("scenario_id")
    )
    if scenario is not None:
        scenario = str(scenario)

    alert_id = str(record.get("source_event_id") or record.get("id") or "")
    timestamp = str(record.get("timestamp") or record.get("saved_at") or "")

    return SOCAlert(
        id=alert_id or "unknown",
        timestamp=timestamp,
        severity=_score_to_severity(score),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        rule_name=rule_name[:512],
        affected_host=affected_host,
        acknowledged=False,
        athena_scenario=scenario,
        payload=record,
    )


def map_wazuh_alert(raw: dict[str, Any]) -> SOCAlert:
    """Map a Wazuh (or Wazuh-like) alert document to SOCAlert."""
    rule = raw.get("rule") if isinstance(raw.get("rule"), dict) else {}
    agent = raw.get("agent") if isinstance(raw.get("agent"), dict) else {}

    alert_id = str(raw.get("id") or raw.get("_id") or raw.get("alert_id") or "")
    timestamp = str(raw.get("timestamp") or raw.get("@timestamp") or "")
    level = int(rule.get("level") or raw.get("level") or 0)
    severity = raw.get("severity") if raw.get("severity") in SEVERITY_ORDER else _level_to_severity(level)
    source = raw.get("source") if raw.get("source") in ALERT_SOURCES else _detect_source(raw)
    rule_name = str(
        rule.get("description")
        or raw.get("ruleName")
        or raw.get("rule_name")
        or f"Rule {rule.get('id', 'unknown')}"
    )
    affected_host = str(
        agent.get("name")
        or agent.get("ip")
        or raw.get("affectedHost")
        or raw.get("affected_host")
        or raw.get("host")
        or "unknown"
    )
    scenario = map_athena_scenario(raw)
    acknowledged = bool(raw.get("acknowledged", False))

    return SOCAlert(
        id=alert_id or "unknown",
        timestamp=timestamp,
        severity=severity,  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        rule_name=rule_name,
        affected_host=affected_host,
        acknowledged=acknowledged,
        athena_scenario=scenario,
        payload=raw,
    )


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def filter_alerts(
    alerts: list[SOCAlert],
    *,
    severity: str | None = None,
    source: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
) -> list[SOCAlert]:
    """Filter SOC alerts by severity (comma-separated), source, and time range."""
    severity_set: set[str] | None = None
    if severity:
        severity_set = {s.strip().lower() for s in severity.split(",") if s.strip()}

    from_dt = _parse_ts(from_ts)
    to_dt = _parse_ts(to_ts)

    out: list[SOCAlert] = []
    for alert in alerts:
        if severity_set and alert.severity not in severity_set:
            continue
        if source and alert.source != source:
            continue
        if from_dt or to_dt:
            alert_dt = _parse_ts(alert.timestamp)
            if alert_dt is None:
                continue
            if from_dt and alert_dt < from_dt:
                continue
            if to_dt and alert_dt > to_dt:
                continue
        out.append(alert)
    return out
