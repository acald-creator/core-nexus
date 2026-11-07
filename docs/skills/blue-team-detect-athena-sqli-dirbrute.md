---
name: Detect Athena SQLi and Dir-Bruteforce
description: Analyst playbook for detecting Athena-labeled SQLi and directory brute-force via Suricata (SIDs, capture path, GT correlation, FP notes)
tags: [blue-team, suricata, athena, sqli, directory-bruteforce, detection]
inclusion: manual
---

## When to Apply
- Answering “did Suricata catch Athena SQLi / dir-bruteforce?”
- Triaging `eve.json` / Vector / Gateway alerts that mention NEXUS Athena SIDs
- Writing or reviewing purple-team detection coverage for Juice Shop–style HTTP stimulation
- Onboarding analysts to Days 16–25 lab detections (not Emerging Threats)

## Approach

### 1. Confirm capture path first
Athena traffic only alerts if Suricata sniffs the path the packets take.
1. DaemonSet must include lab ifaces (`eth0`, `vznat`, `cni0` on Rancher Desktop).
2. Prefer **in-cluster** probes to `host.docker.internal:<lab-port>` over host-native curls.
3. After ConfigMap/DaemonSet restart, wait **~25s** before probing (engine up ≠ inspect-ready).
4. `HTTP_PORTS` must include lab ports (**3003** Juice Shop, 3000/3001, 8090, 5173, …).

### 2. Separate beacons from attacks
| Role | SIDs | Meaning |
|------|------|---------|
| **Beacon** (policy) | 20261601, 20261602 | Athena labeled HTTP / `athena-agents/` UA present (limited 1/src/120s) |
| **SQLi attack** | 20261603, 20262201–203 | Payload patterns **and** `X-Athena-Scenario` |
| **Dir-bruteforce** | 20262401–203 | Storm UA threshold + UA-gated sensitive paths |

Labeled traffic alone is **not** a web-application attack. Prefer attack SIDs for “caught the technique.”

### 3. Detect Athena SQLi (T1190-ish lab)
**What Athena sends (lab):**
- Login POST JSON: `' OR 1=1--` / `OR 1=1` in body → `/rest/user/login`
- Search GET with encoded quote: `/rest/products/search?...%27...`

**What to look for in Suricata:**

| SID | Match | Notes |
|-----|-------|-------|
| 20262201 | body `OR 1=1` + Athena header | Login tautology |
| 20262202 | body `' OR` … `--` + Athena header | Classic quote-OR comment |
| 20262203 | `http.uri.raw` search path + `%27` + Athena header | Use **raw** URI — normalized `http.uri` turns `%27` → `'` |
| 20261603 | URI `OR`+`1=1` + Athena header | Coarse; body rules are stronger for POST login |

**Quick verify:** `scripts/day22-athena-sqli-rules.sh` (after multi-iface Day 21 path is healthy).

### 4. Detect Athena directory brute-force (T1595)
**What Athena sends:**
- UA: `athena-agents/dir-bruteforce`
- Headers: `X-Athena-Scenario`, `X-Athena-Scenario-Id`, `X-Athena-Run-ID`
- Wordlist GETs (admin, `.git`, `wp-admin`, …) — capped in-tool

**What to look for:**

| SID | Match | Notes |
|-----|-------|-------|
| 20262401 | UA storm (`threshold both`, 8/30s) | Campaign signal — not 1:1 with GET count |
| 20262402 | UA + URI `/.git` | Probe indicator |
| 20262403 | UA + URI `/wp-admin` | Probe indicator |

**Quick verify:** `scripts/day24-dir-bruteforce-suricata.sh` then FP check `scripts/day25-suricata-fp-tune.sh`.

### 5. Correlate with ground truth
1. Match `X-Athena-Scenario-Id` / `X-Athena-Run-ID` from GT JSONL to Suricata `http` headers or nearby timestamps.
2. Expect dual-iface **duplicate** alerts (same SID ×2) — count order-of-magnitude, not exact uniqueness.
3. Juice Shop SPA often returns **200** for missing paths → path SIDs mean *probe*, not *exposure*.

### 6. Triage decision tree
```
Beacon only (61601/61602)?
  → Athena present; look for attack SIDs in same window.
SQLi SID without Athena header?
  → Should not fire post–Day 25; if it does, rule drift / old rev.
Dirbrute path SID without dir-bruteforce UA?
  → Should not fire post–Day 25.
20262401 once per GET?
  → Pre–Day 25 rules still loaded; re-apply ConfigMap + restart (ns soc).
Zero alerts after known-good probe?
  → Capture path / HTTP_PORTS / settle time — not “rule logic wrong” first.
```

## Key Patterns
- Rules live in `deploy/kubernetes/system/suricata/suricata-config.yaml` → `athena.rules`
- Apply: `kubectl apply -k deploy/kubernetes/system/suricata -n soc`
- Inspect: `kubectl -n soc exec -c log-tail <pod> -- grep '"signature_id":2026' /var/log/suricata/eve.json`
- Tool: `athena-agents` `dir-bruteforce` + labeled `http-request` / Day 21 Juice Shop Job
- Related skills (narrow): HTTP labels, multi-iface, SQLi body, dirbrute Suricata, FP tune

## Pitfalls
- Host-only tool success ≠ Suricata visibility
- Matching `%27` on normalized `http.uri`
- Treating SPA **200** as confirmed sensitive-path exposure
- Expecting per-request label alerts after Day 25 limits
- Applying Suricata ConfigMap to wrong namespace (`default` vs **`soc`**)

## References
- `docs/skills/blue-team-suricata-multi-iface-capture.md`
- `docs/skills/blue-team-athena-sqli-body-rules.md`
- `docs/skills/blue-team-athena-dirbrute-suricata.md`
- `docs/skills/blue-team-athena-suricata-fp-tune.md`
- `docs/skills/blue-team-athena-suricata-http-labels.md`
- `docs/skills/red-team-athena-dir-bruteforce.md`
- Challenge Days 21–25 in `docs/100-days-challenge.md`
