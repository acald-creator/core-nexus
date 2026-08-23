# Athena — Adversary Emulation Platform

Athena is the controlled red-team and adversary emulation component of Underground Nexus.
It generates labeled attack traffic against approved targets for SOC validation, detection
engineering, and AI-SOC model evaluation.

## Repositories

| Repository | Purpose |
|------------|---------|
| `nexus-athena` | Container image (Kali-based offensive tooling), deploy manifests, runtime profiles |
| `athena-agents` | LLM-driven OPAR agent loop, tool registry, ground-truth emission, ICS safety controls |

## Architecture

See `docs/architecture/08-athena-adversary-fuzzer.md` for the full evolution roadmap.
See `docs/architecture/11-ai-native-integration-principles.md` Section 4 for LLM agent integration.

### Execution Modes

| Mode | Description | Driven by |
|------|-------------|-----------|
| Manual | Analyst drives Kali tools via CLI | Human operator |
| Scripted | Deterministic scenario replay | Scenario config files |
| Autonomous (LLM) | OPAR loop with LLM planning and safety controls | `athena-agents` orchestrator |

### Runtime Profiles

| Profile | Purpose | Capabilities |
|---------|---------|-------------|
| `athena-standard` | Basic red-team commands | Unprivileged |
| `athena-packet-lab` | Packet capture, Wireshark | `NET_ADMIN`, `NET_RAW` |
| `athena-exploit-lab` | Metasploit, exploit simulation | Isolated network, explicit approval |
| `athena-agent` | LLM-driven autonomous emulation | Network to LLM endpoint |
| `athena-agent-ics` | Autonomous ICS/OT testing | `ICS_WRITE`, `CAN_INJECT` + agent |

### Deploy Assets (in `nexus-athena`)

- `deploy/compose/athena-profiles.yml` — Docker Compose with profile selection
- `deploy/kubernetes/base/` — Kubernetes base manifests
- `deploy/kubernetes/overlays/local/` — Local dev overlay
- `deploy/kubernetes/overlays/prod/` — Production overlay
- `scripts/run-athena-profile.sh` — Profile launcher script
- `config/targets/grimoire.toml` / `grimoire-lab.toml` — Grimoire workbench API (host `:3010` or `grimoire.lab:3000`)

## Dockerfile (Platform Reference)

The `Dockerfile` in this directory is a **minimal platform reference** for the Athena
component — it demonstrates the baseline Kali image with unprivileged execution.
The canonical build images live in `nexus-athena/Dockerfile` and `nexus-athena/Dockerfile.arm64`.

## Integration with SOC Pipeline

```
athena-agents (OPAR) → nexus-athena (tooling) → lab network → suricata/wazuh → AI-SOC triage
                                                      ↓
                                              ground-truth records → MinIO → model evaluation
```

## Safety Controls

- Allowlist verification (SHA-256 hash) before each execution cycle
- Per-target rate limiting (token bucket)
- Capability gates (tools declare required caps, profiles grant them)
- ICS safe-range boundary enforcement for write operations
- Traffic labeling (`X-Athena-Scenario`, `X-Athena-Run-ID`) for SOC filtering
- `needs_review` flag halts autonomous execution for human approval

## Supply Chain

- `cosign.pub` in `nexus-athena` — public key for image verification
- `athena0-latest.spdx` — SBOM for latest published image
- CI signs images on push to main via GitHub Actions + cosign
