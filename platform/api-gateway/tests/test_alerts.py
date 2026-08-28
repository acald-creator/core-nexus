"""Alert mapping and filter property tests (Properties 5–7)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings, strategies as st

from src.models.alerts import SOCAlert
from src.services.alerts import (
    clamp_limit,
    filter_alerts,
    map_athena_scenario,
    map_wazuh_alert,
)

SEVERITIES = ["critical", "high", "medium", "low", "informational"]
SOURCES = ["wazuh", "suricata"]


def _soc_alert(
    *,
    severity: str = "high",
    source: str = "wazuh",
    timestamp: str = "2026-08-28T12:00:00+00:00",
    scenario: str | None = None,
    alert_id: str = "a1",
) -> SOCAlert:
    return SOCAlert(
        id=alert_id,
        timestamp=timestamp,
        severity=severity,  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        rule_name="Test rule",
        affected_host="host-1",
        athena_scenario=scenario,
        payload={},
    )


@given(st.integers())
@settings(max_examples=100)
def test_property_6_limit_clamping(limit: int):
    clamped = clamp_limit(limit)
    assert 1 <= clamped <= 500


def test_clamp_limit_default():
    assert clamp_limit(None) == 100


@given(
    severities=st.lists(st.sampled_from(SEVERITIES), min_size=0, max_size=5, unique=True),
    source=st.one_of(st.none(), st.sampled_from(SOURCES)),
    use_from=st.booleans(),
    use_to=st.booleans(),
)
@settings(max_examples=80)
def test_property_5_filter_correctness(severities, source, use_from, use_to):
    base = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    alerts = [
        _soc_alert(
            alert_id=f"a{i}",
            severity=SEVERITIES[i % len(SEVERITIES)],
            source=SOURCES[i % 2],
            timestamp=(base + timedelta(hours=i)).isoformat(),
        )
        for i in range(12)
    ]

    severity_param = ",".join(severities) if severities else None
    from_ts = (base + timedelta(hours=2)).isoformat() if use_from else None
    to_ts = (base + timedelta(hours=8)).isoformat() if use_to else None

    result = filter_alerts(
        alerts,
        severity=severity_param,
        source=source,
        from_ts=from_ts,
        to_ts=to_ts,
    )

    severity_set = set(severities) if severities else None
    from_dt = datetime.fromisoformat(from_ts) if from_ts else None
    to_dt = datetime.fromisoformat(to_ts) if to_ts else None

    for alert in result:
        if severity_set:
            assert alert.severity in severity_set
        if source:
            assert alert.source == source
        if from_dt or to_dt:
            ts = datetime.fromisoformat(alert.timestamp)
            if from_dt:
                assert ts >= from_dt
            if to_dt:
                assert ts <= to_dt

    for alert in alerts:
        matches = True
        if severity_set and alert.severity not in severity_set:
            matches = False
        if source and alert.source != source:
            matches = False
        if from_dt or to_dt:
            ts = datetime.fromisoformat(alert.timestamp)
            if from_dt and ts < from_dt:
                matches = False
            if to_dt and ts > to_dt:
                matches = False
        if matches:
            assert alert in result


@given(
    scenario=st.one_of(st.none(), st.text(min_size=1, max_size=40).filter(lambda s: s.strip())),
    location=st.sampled_from(["top", "data", "headers"]),
)
@settings(max_examples=60)
def test_property_7_athena_scenario_preservation(scenario, location):
    raw: dict = {
        "id": "42",
        "timestamp": "2026-08-28T12:00:00Z",
        "rule": {"level": 10, "description": "SQLi attempt", "groups": ["web"]},
        "agent": {"name": "juice-shop"},
        "data": {},
    }
    if scenario:
        if location == "top":
            raw["X-Athena-Scenario"] = scenario
        elif location == "data":
            raw["data"]["X-Athena-Scenario"] = scenario
        else:
            raw["data"]["headers"] = {"X-Athena-Scenario": scenario}

    extracted = map_athena_scenario(raw)
    mapped = map_wazuh_alert(raw)

    if scenario:
        assert extracted == scenario
        assert mapped.athena_scenario == scenario
    else:
        assert extracted is None
        assert mapped.athena_scenario is None


def test_map_wazuh_alert_level_and_suricata_group():
    raw = {
        "id": "99",
        "timestamp": "2026-08-28T15:00:00Z",
        "rule": {"level": 15, "description": "ET SCAN", "groups": ["suricata", "ids"]},
        "agent": {"name": "sensor-1"},
    }
    alert = map_wazuh_alert(raw)
    assert alert.severity == "critical"
    assert alert.source == "suricata"
    assert alert.rule_name == "ET SCAN"
    assert alert.affected_host == "sensor-1"


@pytest.mark.asyncio
async def test_alerts_route_maps_and_filters(client, app, make_token):
    app.state.wazuh_client.get_alerts.return_value = {
        "data": {
            "affected_items": [
                {
                    "id": "1",
                    "timestamp": "2026-08-28T12:00:00+00:00",
                    "rule": {"level": 12, "description": "High alert", "groups": ["web"]},
                    "agent": {"name": "host-a"},
                    "data": {"X-Athena-Scenario": "juice-shop-day11"},
                },
                {
                    "id": "2",
                    "timestamp": "2026-08-28T12:05:00+00:00",
                    "rule": {"level": 5, "description": "Low noise", "groups": ["syscheck"]},
                    "agent": {"name": "host-b"},
                },
            ],
            "total_affected_items": 2,
        }
    }

    token = make_token()
    response = await client.get(
        "/api/v1/alerts?severity=critical,high",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["alerts"]) == 1
    alert = body["alerts"][0]
    assert alert["id"] == "1"
    assert alert["severity"] == "high"
    assert alert["ruleName"] == "High alert"
    assert alert["affectedHost"] == "host-a"
    assert alert["athenaScenario"] == "juice-shop-day11"


@pytest.mark.asyncio
async def test_alerts_route_502_when_wazuh_down(client, app, make_token):
    app.state.wazuh_client.get_alerts.side_effect = RuntimeError("down")
    token = make_token()
    response = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_triage_404_and_504(client, app, make_token):
    import httpx

    token = make_token()
    app.state.ai_inference_client.get_triage.return_value = None
    r404 = await client.get(
        "/api/v1/alerts/abc/triage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r404.status_code == 404

    app.state.ai_inference_client.get_triage.side_effect = httpx.TimeoutException("timeout")
    r504 = await client.get(
        "/api/v1/alerts/abc/triage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r504.status_code == 504
