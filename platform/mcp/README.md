# Nexus MCP

Model Context Protocol tool bridge for Underground Nexus. Exposes SOC tools and platform context to MCP-compatible clients.

## Current Tools

| Tool | Description |
|------|-------------|
| query_soc_memory | Search AI-SOC vector memory for triaged alerts |
| get_inference_hardware | Scan inference node GPU/CPU capabilities |
| get_active_models | List active AI models in the inference engine |

## How It Works

Translates MCP tool calls into HTTP requests against platform backends.

Connected: AI Inference (:8000)
Planned: Wazuh API (:55000), MinIO (:9000), athena-agents

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| AI_INFERENCE_URL | http://ai-inference.soc.svc.cluster.local:8000 | AI Inference endpoint |
| PORT | 3001 | Listen port |

## Planned Tools

| Tool | Description |
|------|-------------|
| query_wazuh_alerts | Search security alerts with filters |
| get_alert_triage | Get AI triage for an alert |
| list_skills | Browse agent skill library |
| list_artifacts | Browse PCAPs, SBOMs, sessions |
| get_agent_status | Check OPAR agent session state |
| approve_action | Approve a needs_review agent action |
| trigger_scenario | Start an Athena agent scenario |

## Build

    npm install && npm run build && npm start

Image: Chainguard Node.js (minimal, non-root, multi-stage).

## Transport

SSE via @modelcontextprotocol/sdk:
- GET /sse - establish connection
- POST /messages - send tool invocations

Compatible with: Kiro, Claude Desktop, any MCP SDK client.

## Cross-References

- docs/architecture/07-mcp-workbench.md
- docs/architecture/11-ai-native-integration-principles.md Section 2
- nexus-webtop-workbench (MCP client)
- platform/ai-inference/ (backend)
