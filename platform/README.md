# Platform Components

Implementation code for Underground Nexus. Architecture docs live in `docs/`.

| Path | Role |
|------|------|
| `api-gateway/` | FastAPI gateway (JWT, upstream clients, Vault AppRole hydrate) |
| `nexus-console/` | React Console (launchpad, Agent Feed, settings) |
| `ai-inference/` | Triage / enrichment service |
| `mcp/` | Nexus MCP server |
| `workbench/` | Jupyter workbench image + Vault consumer example |
| `athena/` | Athena container reference (images in `nexus-athena`) |
| `soc/` | SOC notes — headless stack in `deploy/kubernetes/soc/` |
| `sensors/` | Sensor notes — Suricata in `deploy/kubernetes/system/suricata` |

Local run: `./scripts/dev-stack.sh up --from-vault` (Vault from `nexus-hashistack`).
Images: `./scripts/build-platform-images.sh` → `phoenixvlabs/nexus-*`.
