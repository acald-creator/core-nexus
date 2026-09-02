# Nexus Console

Primary Platform UI for Underground Nexus — React/Vite launchpad for SOC alerts,
approvals, Athena agent feed, artifacts, and lab deep-links (ADR 0006).

## Purpose

Nexus Console is the blue-team browser surface. Prefer it over retired webtops.
Companion surfaces: Jupyter purple workbench, isolated Athena (`athena-agents` /
`nexus-athena`), optional `nexus-tui`.

## Stack

- **Framework:** React 19 + TypeScript
- **Build tool:** Vite
- **Linting:** ESLint with TypeScript-aware rules
- **Container:** `nginxinc/nginx-unprivileged` on port **8080**

## Development

```bash
cd platform/nexus-console
npm install
npm run dev   # Vite :5173 — set VITE_API_GATEWAY_URL if gateway is not :3100
```

## Build & Deploy

```bash
npm run build
docker build -t local/nexus-console:latest .
# K8s Service maps 80 → container 8080; compose should publish 3000:8080
```

Hybrid-sensor labs list alerts from ai-inference triage (`NEXUS_GW_ALERTS_SOURCE=triage`).
Full-SIEM labs can still use Wazuh via the gateway (`overlays/test`).

## Architecture References

- `docs/architecture/01-component-architecture.md` — Console as primary UI
- `docs/decisions/0006-human-client-surfaces.md` — Console + Jupyter + Athena
- `docs/decisions/0011-compose-soc-vector-zeek-falco-tetragon.md` — hybrid sensor stack

## Relationship to Other Interfaces

| Interface | Purpose | Environment |
|-----------|---------|-------------|
| Nexus Console (this) | Blue launchpad: alerts, approvals, feed, artifacts | Browser |
| Jupyter Workbench | Purple analyst / MCP workspace | Browser (`:8888`) |
| Athena / athena-agents | Isolated red stimulation & emulation | Container / lab net |
| nexus-tui | Terminal SOC console | SSH / air-gapped |
| Wazuh (optional) | Full-SIEM path only — not required for hybrid-sensor | Cluster API via gateway |
