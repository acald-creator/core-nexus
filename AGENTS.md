# Agent Instructions

Use `docs/00-ai-collaboration.md` as the canonical instruction set for AI-assisted work in this repository.

## Repository Role

Architecture hub for Underground Nexus. Contains platform component definitions,
deployment manifests, numbered architecture documents, and cross-repo integration docs.

## Key References

- `docs/architecture/` — numbered architecture docs (source of truth)
- `docs/00-ai-collaboration.md` — shared vocabulary, model roles, non-negotiable decisions
- `platform/` — component definitions (athena, soc, workbench, sensors, ai-inference, mcp)
- `deploy/` — compose, kubernetes, UDS manifests

## Agent Expectations

- Prefer direct file edits when the user asks for implementation or documentation changes.
- Preserve the numbered document order in `docs/architecture/`.
- Keep near-term Kubernetes/UDS work separate from future Enterprise Platform/SecureOS work.
- After edits, check for terminology drift against `docs/00-ai-collaboration.md` Section 3.
- Summarize changed files and remaining risks.
- When working on LLM agent workflows, reference `athena-agents` for implementation details
  and update architecture docs here for integration narrative.
- Check `docs/skills/` (git-based) or `~/.kiro/skills/` (local) for applicable skills before starting novel work.
- After solving novel problems, add or update skills in `docs/skills/` and run `scripts/sync-skills.sh push-local`.

## Cross-Repo Context

| Repository | Relationship |
|------------|-------------|
| `athena-agents` | LLM-driven adversary emulation framework (OPAR loop) |
| `nexus-athena` | Red-team container image and execution environment |
| `nexus-webtop-soc` | SOC analyst webtop + baseline compose stack |
| `nexus-webtop-workbench` | Analyst workbench desktop image |

## Guardrails

- Do not add SOC control-plane services into desktop images.
- Do not add offensive tooling here — it belongs in `nexus-athena` or `athena-agents`.
- LLM agents must operate within allowlist and capability-gate constraints.
- Autonomous response is a later capability; human approval comes first.
- Keep credentials and certificates out of committed files.
