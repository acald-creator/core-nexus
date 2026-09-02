"""NumPy triage scorer with Suricata / Wazuh / Athena feature pack (E2)."""
from __future__ import annotations

import hashlib
import time
from typing import Any

import numpy as np


ATHENA_KEYS = (
    "X-Athena-Scenario",
    "x-athena-scenario",
    "X-Athena-Scenario-Id",
    "x-athena-scenario-id",
    "athena_scenario",
    "athenaScenario",
)

# Feature layout (weights must match length):
# 0 severity, 1 port/rule risk, 2 signature/text risk,
# 3 category/groups risk, 4 athena/training context
FEATURE_NAMES = (
    "severity",
    "port_or_rule_risk",
    "signature_or_text_risk",
    "category_or_groups",
    "athena_context",
)


class TriageModel:
    def __init__(self):
        self.model_name = "nexus-triage-baseline"
        self.model_version = "1.1.0"
        self.model_digest = hashlib.sha256(
            b"nexus-triage-baseline-v1.1.0-weights-e2"
        ).hexdigest()
        self.threshold = 0.65
        self.weights = np.array([0.35, 0.20, 0.20, 0.15, 0.10], dtype=float)

    def _extract_athena_scenario(self, event: dict[str, Any]) -> str | None:
        for key in ATHENA_KEYS:
            if event.get(key):
                return str(event[key])
        data = event.get("data")
        if isinstance(data, dict):
            for key in ATHENA_KEYS:
                if data.get(key):
                    return str(data[key])
            headers = data.get("headers") or data.get("http_headers")
            if isinstance(headers, dict):
                lowered = {str(k).lower(): v for k, v in headers.items()}
                if lowered.get("x-athena-scenario"):
                    return str(lowered["x-athena-scenario"])
                if lowered.get("x-athena-scenario-id"):
                    return str(lowered["x-athena-scenario-id"])
                if lowered.get("x-athena-label"):
                    return str(lowered["x-athena-label"])
        return None

    def _athena_feature(self, scenario: str | None) -> tuple[float, list[str]]:
        """Training/stimulation traffic is labeled — boost review, don't auto-contain."""
        if not scenario:
            return 0.0, []
        # Presence of Athena label => purple/red range traffic worth reviewing
        return 0.7, [f"Athena scenario label present ({scenario})"]

    def _extract_suricata_features(
        self, event: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], dict[str, Any]]:
        alert = event.get("alert") if isinstance(event.get("alert"), dict) else {}
        severity = int(alert.get("severity", 3) or 3)
        if alert:
            if severity == 1:
                severity_score = 1.0
            elif severity == 2:
                severity_score = 0.6
            else:
                severity_score = 0.3
        else:
            severity_score = 0.1

        dest_port = int(event.get("dest_port") or 0)
        high_risk_ports = {22, 23, 445, 3389, 139, 5900, 2375, 10250}
        port_score = 1.0 if dest_port in high_risk_ports else (0.3 if dest_port > 0 else 0.0)

        sig = str(alert.get("signature") or "").lower()
        category = str(alert.get("category") or "").lower()
        high_risk_keywords = [
            "exploit",
            "cve",
            "shellcode",
            "reverse",
            "malware",
            "scan",
            "bruteforce",
            "trojan",
            "ransomware",
        ]
        keyword_match = any(kw in sig for kw in high_risk_keywords)
        sig_score = 1.0 if keyword_match else (0.2 if sig else 0.0)

        high_risk_categories = {
            "attempted-admin",
            "attempted-user",
            "policy-violation",
            "shellcode-detect",
            "trojan-activity",
            "web-application-attack",
        }
        cat_score = 1.0 if category in high_risk_categories else (0.4 if category else 0.0)

        scenario = self._extract_athena_scenario(event)
        athena_score, athena_explain = self._athena_feature(scenario)

        explanation: list[str] = []
        if alert:
            explanation.append(f"Suricata alert severity {severity}")
        if dest_port in high_risk_ports:
            explanation.append(f"Targeting high-risk port {dest_port}")
        if keyword_match:
            explanation.append("Malicious signature keywords detected")
        if category:
            explanation.append(f"Suricata category '{category}'")
        explanation.extend(athena_explain)

        meta = {
            "suricata_category": category or None,
            "suricata_signature": alert.get("signature"),
            "suricata_signature_id": alert.get("signature_id") or alert.get("sid"),
            "dest_port": dest_port or None,
            "app_proto": event.get("app_proto"),
            "athena_scenario": scenario,
        }
        features = np.array(
            [severity_score, port_score, sig_score, cat_score, athena_score],
            dtype=float,
        )
        return features, explanation, meta

    def _extract_wazuh_features(
        self, event: dict[str, Any]
    ) -> tuple[np.ndarray, list[str], dict[str, Any]]:
        rule = event.get("rule") if isinstance(event.get("rule"), dict) else {}
        level = int(rule.get("level", 0) or 0)
        severity_score = min(level / 15.0, 1.0)

        high_risk_rules = {5710, 5712, 5716, 5720, 5503, 18107}
        try:
            rule_id = int(rule.get("id", 0) or 0)
        except (TypeError, ValueError):
            rule_id = 0
        rule_score = 1.0 if rule_id in high_risk_rules else (0.5 if level >= 7 else 0.1)

        desc = str(rule.get("description") or "").lower()
        high_risk_keywords = [
            "failed",
            "attack",
            "unauthorized",
            "shell",
            "privilege",
            "root",
            "cve",
            "exploit",
            "malware",
        ]
        keyword_match = any(kw in desc for kw in high_risk_keywords)
        desc_score = 1.0 if keyword_match else (0.2 if desc else 0.0)

        groups = rule.get("groups") or []
        if not isinstance(groups, list):
            groups = [groups]
        groups_l = [str(g).lower() for g in groups]
        high_group_tokens = {
            "authentication_failed",
            "exploit_attempt",
            "attack",
            "rootcheck",
            "virus",
            "web",
            "ids",
            "pci_dss",
        }
        group_hit = any(
            any(tok in g for tok in high_group_tokens) for g in groups_l
        )
        # MITRE technique ids sometimes appear under rule.mitre.technique / id
        mitre = rule.get("mitre") if isinstance(rule.get("mitre"), dict) else {}
        mitre_ids: list[str] = []
        for key in ("id", "technique", "tactic"):
            val = mitre.get(key)
            if isinstance(val, list):
                mitre_ids.extend(str(x) for x in val)
            elif val:
                mitre_ids.append(str(val))
        mitre_score = 0.8 if mitre_ids else 0.0
        groups_score = max(1.0 if group_hit else 0.0, mitre_score, 0.3 if groups_l else 0.0)

        scenario = self._extract_athena_scenario(event)
        athena_score, athena_explain = self._athena_feature(scenario)

        explanation: list[str] = []
        if level > 0:
            explanation.append(f"Wazuh alert level {level}")
        if rule_id in high_risk_rules:
            explanation.append(f"Wazuh high-severity rule ID {rule_id}")
        if keyword_match:
            explanation.append("Alert description contains security risk indicators")
        if group_hit:
            explanation.append(f"Wazuh groups indicate risk ({', '.join(groups_l[:4])})")
        if mitre_ids:
            explanation.append(f"MITRE refs: {', '.join(mitre_ids[:4])}")
        explanation.extend(athena_explain)

        meta = {
            "wazuh_rule_id": rule_id or None,
            "wazuh_groups": groups_l,
            "mitre": mitre_ids,
            "athena_scenario": scenario,
        }
        features = np.array(
            [severity_score, rule_score, desc_score, groups_score, athena_score],
            dtype=float,
        )
        return features, explanation, meta

    def triage_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_id = str(
            event.get("event_id")
            or event.get("id")
            or event.get("_id")
            or event.get("alert_id")
            or "unknown-event-id"
        )
        timestamp = str(
            event.get("timestamp") or event.get("date") or event.get("@timestamp") or time.time()
        )

        if isinstance(event.get("alert"), dict) or "dest_port" in event:
            features, explanation, meta = self._extract_suricata_features(event)
            event_type = "Suricata"
        elif isinstance(event.get("rule"), dict) or event.get("rule"):
            features, explanation, meta = self._extract_wazuh_features(event)
            event_type = "Wazuh"
        else:
            features = np.array([0.1, 0.1, 0.1, 0.0, 0.0], dtype=float)
            explanation = ["Generic/unknown event format"]
            meta = {"athena_scenario": self._extract_athena_scenario(event)}
            event_type = "Generic"

        score = float(np.clip(np.dot(features, self.weights), 0.0, 1.0))

        # Athena-labeled traffic: prefer human review over auto-contain wording
        athena_scenario = meta.get("athena_scenario")
        if score < 0.3:
            label = "benign"
            recommended_action = "Allow traffic and monitor logs."
        elif score < 0.6:
            label = "suspicious"
            recommended_action = (
                "Increase telemetry logging frequency and alert on subsequent events."
            )
        elif score < 0.75 or athena_scenario:
            label = "needs_human_review"
            recommended_action = (
                "Expose threat context to analyst workbench for manual inspection."
                + (
                    f" Athena-labeled traffic ({athena_scenario}) — treat as stimulation/emulation until verified."
                    if athena_scenario
                    else ""
                )
            )
        else:
            label = "likely_true_positive"
            recommended_action = (
                "Draft containment policy for human approval: isolate source workload "
                "using a Kubernetes NetworkPolicy (do not auto-apply)."
            )

        reason = " | ".join(explanation) if explanation else "No anomalies detected."
        reason = f"[{event_type}] {reason}"

        return {
            "source_event_id": event_id,
            "timestamp": timestamp,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_digest": self.model_digest,
            "score": round(score, 4),
            "confidenceScore": round(score, 4),
            "label": label,
            "threshold": self.threshold,
            "reason": reason,
            "reasoningExcerpt": reason,
            "features_used": {
                name: round(float(val), 4)
                for name, val in zip(FEATURE_NAMES, features.tolist())
            },
            "recommended_action": recommended_action,
            "recommendedAction": recommended_action,
            "event_type": event_type,
            "athena_scenario": athena_scenario,
            "feature_meta": meta,
        }
