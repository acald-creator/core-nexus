import time
import hashlib
import numpy as np

class TriageModel:
    def __init__(self):
        self.model_name = "nexus-triage-baseline"
        self.model_version = "1.0.0"
        self.model_digest = hashlib.sha256(b"nexus-triage-baseline-v1.0.0-weights").hexdigest()
        self.threshold = 0.65

        # Feature weights for scoring
        # 0: base severity weight
        # 1: port risk weight
        # 2: signature risk weight
        self.weights = np.array([0.5, 0.25, 0.25])

    def _extract_suricata_features(self, event: dict) -> tuple:
        """Extract features from a Suricata alert/flow event."""
        # Feature 0: Severity/Alert existence
        alert = event.get("alert", {})
        severity = alert.get("severity", 3)  # Suricata severity is usually 1 (high) to 3 (low)
        severity_score = 1.0 if alert else 0.1
        if alert and severity == 1:
            severity_score = 1.0
        elif alert and severity == 2:
            severity_score = 0.6
        elif alert:
            severity_score = 0.3

        # Feature 1: Port risk
        dest_port = event.get("dest_port", 0)
        high_risk_ports = {22, 23, 445, 3389, 139}
        port_score = 1.0 if dest_port in high_risk_ports else (0.3 if dest_port > 0 else 0.0)

        # Feature 2: Signature/Payload keywords
        sig = alert.get("signature", "").lower()
        high_risk_keywords = ["exploit", "cve", "shellcode", "reverse", "malware", "scan", "bruteforce"]
        keyword_match = any(kw in sig for kw in high_risk_keywords)
        sig_score = 1.0 if keyword_match else (0.2 if sig else 0.0)

        features = [severity_score, port_score, sig_score]
        explanation = []
        if alert:
            explanation.append(f"Suricata alert severity {severity}")
        if dest_port in high_risk_ports:
            explanation.append(f"Targeting high-risk port {dest_port}")
        if keyword_match:
            explanation.append("Malicious signature keywords detected")

        return np.array(features), explanation

    def _extract_wazuh_features(self, event: dict) -> tuple:
        """Extract features from a Wazuh manager alert."""
        # Feature 0: Rule level (usually 0 to 15+)
        rule = event.get("rule", {})
        level = int(rule.get("level", 0))
        severity_score = min(level / 15.0, 1.0)

        # Feature 1: High-risk rules/ports mentioned
        # Checking destination ports or rule ids
        high_risk_rules = {5710, 5712, 5716, 5720} # ssh brute force/failure rule examples
        rule_id = int(rule.get("id", 0))
        rule_score = 1.0 if rule_id in high_risk_rules else (0.5 if level >= 7 else 0.1)

        # Feature 2: Description text keywords
        desc = rule.get("description", "").lower()
        high_risk_keywords = ["failed", "attack", "unauthorized", "shell", "privilege", "root", "cve"]
        keyword_match = any(kw in desc for kw in high_risk_keywords)
        desc_score = 1.0 if keyword_match else (0.2 if desc else 0.0)

        features = [severity_score, rule_score, desc_score]
        explanation = []
        if level > 0:
            explanation.append(f"Wazuh alert level {level}")
        if rule_id in high_risk_rules:
            explanation.append(f"Wazuh high-severity rule ID {rule_id}")
        if keyword_match:
            explanation.append("Alert description contains security risk indicators")

        return np.array(features), explanation

    def triage_event(self, event: dict) -> dict:
        """Assess the event security risk and return a structured triage output."""
        event_id = event.get("event_id", event.get("id", "unknown-event-id"))
        timestamp = event.get("timestamp", event.get("date", str(time.time())))

        # Determine type of event source
        if "alert" in event or "dest_port" in event:
            features, explanation = self._extract_suricata_features(event)
            event_type = "Suricata"
        elif "rule" in event:
            features, explanation = self._extract_wazuh_features(event)
            event_type = "Wazuh"
        else:
            # Fallback/Generic event parsing
            features = np.array([0.1, 0.1, 0.1])
            explanation = ["Generic/unknown event format"]
            event_type = "Generic"

        # NumPy threat scoring: weighted average of features
        score = float(np.dot(features, self.weights))

        # Assign labels based on score
        if score < 0.3:
            label = "benign"
            recommended_action = "Allow traffic and monitor logs."
        elif score < 0.6:
            label = "suspicious"
            recommended_action = "Increase telemetry logging frequency and alert on subsequent events."
        elif score < 0.75:
            label = "needs_human_review"
            recommended_action = "Expose threat context to analyst workbench for manual inspection."
        else:
            label = "likely_true_positive"
            recommended_action = "Draft containment policy: isolate source workload using a Kubernetes NetworkPolicy."

        reason = " | ".join(explanation) if explanation else "No anomalies detected."

        return {
            "source_event_id": event_id,
            "timestamp": timestamp,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_digest": self.model_digest,
            "score": round(score, 4),
            "label": label,
            "threshold": self.threshold,
            "reason": f"[{event_type}] {reason}",
            "features_used": features.tolist(),
            "recommended_action": recommended_action
        }
