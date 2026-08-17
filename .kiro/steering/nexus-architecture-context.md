---
inclusion: auto
---

# Core Nexus Architecture Context

This workspace is the architecture hub for Underground Nexus. When working here:

## Key Files
- `architecture.md` — canonical architecture guide (always check before structural changes)
- `docs/00-ai-collaboration.md` — AI collaboration norms
- `platform/` — platform component definitions (athena, soc, workbench, sensors, ai-inference, mcp)
- `deploy/` — deployment manifests (compose, kubernetes, UDS)

## Applicable Skills
When working in this repo, the following skills from `~/.kiro/skills/` are most relevant:
- `log-code-bug-analysis.md` — for debugging platform components
- `blue-team-soc-analysis.md` — for SOC baseline stack work
- `red-team-athena-workflow.md` — for Athena platform definitions

## Guardrails
- Keep SOC runtime services out of desktop images
- Keep red-team tooling in Nexus Athena unless admin workflow requires it
- Treat privileged mounts and virtualization as explicit profiles
- Keep near-term K8s/UDS work separate from future Enterprise Platform/SecureOS
