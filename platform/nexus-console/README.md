# Nexus Console

The primary Platform UI for Underground Nexus — a custom React/Vite dashboard serving as
the unified launchpad for all services and tools.

## Purpose

Nexus Console replaces Portainer as the primary interface. It provides a single entry point
for navigating SOC dashboards, workbench environments, Athena controls, MinIO artifacts,
and system status.

## Stack

- **Framework:** React 19 + TypeScript
- **Build tool:** Vite
- **Linting:** ESLint with TypeScript-aware rules
- **Container:** Dockerfile for production builds

## Development

```bash
cd platform/nexus-console
npm install
npm run dev
```

## Build & Deploy

```bash
# Build production bundle
npm run build

# Build container image
docker build -t local/nexus-console:latest .
```

## Architecture References

- `docs/architecture/01-component-architecture.md` — Nexus Console in Decision Register as Primary UI
- `docs/architecture/03-phased-implementation-roadmap.md` — Phase 1: Primary UI replaced with Nexus Console

## Relationship to Other Interfaces

| Interface | Purpose | Environment |
|-----------|---------|-------------|
| Nexus Console (this) | Unified web launchpad for all services | Browser (any) |
| Analyst Workbench | JupyterLab agentic workspace for investigations | Browser (any) |
| nexus-tui | Terminal SOC console for alert triage and agent monitoring | SSH / air-gapped |
| Wazuh Dashboard | Security event investigation | Browser (via Nexus Console link) |
