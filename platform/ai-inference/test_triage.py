"""Unit tests for triage feature pack + SQLite store (E0–E2)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from store import TriageStore
from triage import TriageModel


def test_suricata_category_and_athena_review():
    model = TriageModel()
    result = model.triage_event(
        {
            "id": "suri-1",
            "dest_port": 445,
            "alert": {
                "severity": 1,
                "signature": "ET EXPLOIT Possible SMB scan",
                "category": "trojan-activity",
            },
            "X-Athena-Scenario": "juice-shop-day11",
        }
    )
    assert result["event_type"] == "Suricata"
    assert result["confidenceScore"] == result["score"]
    assert result["recommendedAction"] == result["recommended_action"]
    assert result["athena_scenario"] == "juice-shop-day11"
    assert result["label"] == "needs_human_review"
    assert "human" in result["recommended_action"].lower() or "analyst" in result["recommended_action"].lower()
    assert "containment" not in result["recommended_action"].lower() or "approval" in result["recommended_action"].lower()


def test_athena_scenario_id_header_review():
    model = TriageModel()
    result = model.triage_event(
        {
            "id": "suri-2",
            "dest_port": 8090,
            "technique": "T1046",
            "alert": {
                "severity": 1,
                "signature": "GET /api/v1/novels",
                "category": "trojan-activity",
            },
            "X-Athena-Scenario-Id": "night-quire-recon-run",
        }
    )
    assert result["athena_scenario"] == "night-quire-recon-run"
    assert result["scenario_id"] == "night-quire-recon-run"
    assert result["technique"] == "T1046"
    assert result["label"] == "needs_human_review"


def test_list_recent_triage_store():
    model = TriageModel()
    with tempfile.TemporaryDirectory() as tmp:
        store = TriageStore(db_path=Path(tmp) / "t.db")
        event = {
            "id": "list-1",
            "dest_port": 443,
            "alert": {"severity": 2, "signature": "test", "category": "web-application-attack"},
        }
        store.upsert(model.triage_event(event))
        recent = store.recent(limit=5)
        assert any(r.get("source_event_id") == "list-1" for r in recent)


def test_athena_scenario_label_header_review():
    model = TriageModel()
    result = model.triage_event(
        {
            "id": "suri-3",
            "dest_port": 8090,
            "alert": {
                "severity": 1,
                "signature": "ET SCAN probe",
                "category": "trojan-activity",
            },
            "X-Athena-Scenario": "night-quire",
        }
    )
    assert result["athena_scenario"] == "night-quire"
    assert result["label"] == "needs_human_review"

def test_wazuh_groups_and_mitre():
    model = TriageModel()
    result = model.triage_event(
        {
            "id": "wazuh-9",
            "rule": {
                "id": 5710,
                "level": 10,
                "description": "sshd: authentication failed",
                "groups": ["authentication_failed", "sshd"],
                "mitre": {"id": ["T1110"]},
            },
        }
    )
    assert result["event_type"] == "Wazuh"
    assert result["score"] >= 0.6
    assert "MITRE" in result["reason"] or "mitre" in result["reason"].lower()
    assert result["features_used"]["category_or_groups"] > 0


def test_high_score_without_athena_can_request_human_approved_containment():
    model = TriageModel()
    result = model.triage_event(
        {
            "id": "suri-hot",
            "dest_port": 445,
            "alert": {
                "severity": 1,
                "signature": "ET EXPLOIT reverse shellcode ransomware",
                "category": "shellcode-detect",
            },
        }
    )
    assert result["athena_scenario"] is None
    assert result["label"] == "likely_true_positive"
    assert "human approval" in result["recommended_action"].lower()


def test_store_upsert_get_search():
    with tempfile.TemporaryDirectory() as tmp:
        store = TriageStore(db_path=Path(tmp) / "t.db")
        model = TriageModel()
        scored = model.triage_event(
            {
                "id": "abc-123",
                "rule": {"id": 1, "level": 3, "description": "low noise"},
            }
        )
        scored["saved_at"] = 1.0
        store.upsert(scored)
        got = store.get("abc-123")
        assert got is not None
        assert got["source_event_id"] == "abc-123"
        assert store.count() == 1
        hits = store.search("Wazuh level", limit=5)
        assert len(hits) >= 1
