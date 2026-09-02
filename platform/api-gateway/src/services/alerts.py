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


def _detect_source(raw: dict[str, Any]) -> str:
    rule = raw.get("rule") if isinstance(raw.get("rule"), dict) else {}
    groups = rule.get("groups") or []
    if isinstance(groups, list) and any("suricata" in str(g).lower() for g in groups):
        return "suricata"
    decoder = raw.get("decoder")
    if isinstance(decoder, dict) and "suricata" in str(decoder.get("name", "")).lower():
        return "suricata"
    if str(raw.get("source", "")).lower() == "suricata":
        return "suricata"
    return "wazuh"


def map_wazuh_alert(raw: dict[str, Any]) -> SOCAlert:
    """Map a Wazuh (or Wazuh-like) alert document to SOCAlert."""
    rule = raw.get("rule") if isinstance(raw.get("rule"), dict) else {}
    agent = raw.get("agent") if isinstance(raw.get("agent"), dict) else {}

    alert_id = str(raw.get("id") or raw.get("_id") or raw.get("alert_id") or "")
    timestamp = str(raw.get("timestamp") or raw.get("@timestamp") or "")
    level = int(rule.get("level") or raw.get("level") or 0)
    severity = raw.get("severity") if raw.get("severity") in SEVERITY_ORDER else _level_to_severity(level)
    source = raw.get("source") if raw.get("source") in ("wazuh", "suricata") else _detect_source(raw)
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
