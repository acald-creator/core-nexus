# Workbench

This directory contains JupyterLab-based agentic workspace integration assets.

## Current Implementation

The analyst workbench exists at two levels:

| Asset | Location | Purpose |
|-------|----------|---------|
| Desktop image | `nexus-webtop-workbench` repo | Browser-based analyst desktop (recommended) |
| JupyterLab integration | This directory | MCP client examples, Vault integration, notebooks |
| Legacy webtop | `nexus-webtop-soc` repo | XFCE desktop (being superseded) |

### What's here

- `Dockerfile` — JupyterLab-based workbench container
- `requirements.txt` — Python dependencies
- `mcp_client_example.ipynb` — Example notebook for MCP server interaction
- `vault_example.py` — Vault integration example

## Architecture References

- `docs/architecture/01-component-architecture.md` Section 3 — Workbench refinement goals
- `docs/architecture/07-mcp-workbench.md` — MCP server and purple-team MLOps workbench
- `docs/architecture/11-ai-native-integration-principles.md` Section 2 — Agentic Workspace (MCP)

## Naming Clarification

- **`nexus-webtop-workbench`** (separate repo) — the container image for the browser-based analyst desktop
- **`platform/workbench/`** (this directory) — JupyterLab integration code and notebooks for the agentic workspace
- Both serve the "analyst workbench" role; the separate repo builds the image, this directory provides the integration layer
