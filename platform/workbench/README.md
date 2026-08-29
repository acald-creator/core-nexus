# Workbench

JupyterLab-based **purple** agentic workspace — evaluate detections/models against
Athena ground truth, use MCP clients, and keep red tooling out of this image.

## Canonical surface

| Asset | Location | Purpose |
|-------|----------|---------|
| JupyterLab workbench | `platform/workbench/` (this directory) + published image | Purple human client |
| Nexus Console | `platform/nexus-console/` | Blue/ops UI (deep-links; not a desktop OS) |
| Athena | `nexus-athena` / `athena-agents` | Isolated red range |

Full Linux webtop images (`nexus-webtop-workbench`, `nexus-webtop-soc`) are **retired**
as product surfaces. See `docs/architecture/01-component-architecture.md` §0.

### What's here

- `Dockerfile` — JupyterLab-based workbench container
- `requirements.txt` — Python dependencies
- `mcp_client_example.ipynb` — Example notebook for MCP server interaction
- `vault_example.py` — Vault integration example

## Architecture References

- `docs/architecture/01-component-architecture.md` §0 (narrative) and Workbench section
- `docs/architecture/07-mcp-workbench.md` — MCP server and purple-team MLOps workbench
- `docs/architecture/11-ai-native-integration-principles.md` Section 2 — Agentic Workspace (MCP)

## Naming

- **Workbench** = Jupyter purple workspace (this directory / image).
- **Console** = web ops/SOC UI.
- Do not reintroduce XFCE/MATE webtops as the recommended analyst path.
