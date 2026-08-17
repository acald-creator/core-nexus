# Agent Skills Library

Portable, versioned skill files for AI agents across the Underground Nexus ecosystem.

## Purpose

Skills encode proven approaches to repeatable problems. They eliminate redundant
LLM reasoning by providing the method, patterns, and pitfalls upfront — saving
tokens and improving consistency across sessions and tools.

## How Skills Are Used

| Tool | Read from | Write to |
|------|-----------|----------|
| Kiro | `~/.kiro/skills/` (symlink or sync from here) | Auto-generated via Stop hook |
| Claude Code / Codex | Referenced in `AGENTS.md` / `CLAUDE.md` | Manual or post-session script |
| athena-agents OPAR | Loaded from MinIO `nexus-memory/skills/` at Plan phase | Written at Reflect phase |
| Any LLM via API | Injected into system prompt by wrapper | Captured by wrapper output |

## Sync

Skills are synchronized across three locations:

```
core-nexus/docs/skills/    ← git (versioned, portable, source of truth)
~/.kiro/skills/            ← local (Kiro reads from here)
MinIO nexus-memory/skills/ ← platform (headless agents read from here)
```

Use `scripts/sync-skills.sh` to push/pull between locations.

## Skill Format

```markdown
---
name: <Skill Name>
description: <One-line summary>
tags: [<domain>, <sub-domain>]
inclusion: manual
---

## When to Apply
<conditions that indicate this skill is relevant>

## Approach
<numbered steps>

## Key Patterns
<specific commands, code patterns, or indicators>

## Pitfalls
<what to avoid>

## References
<paths, tools, links>
```

## Domains

| Domain | Covers |
|--------|--------|
| `red-team` | Athena offensive workflows, adversary emulation |
| `blue-team` | SOC analysis, detection engineering, incident response |
| `ics-ot` | Modbus, CAN Bus, SCADA protocols |
| `log-analysis` | Log parsing, debugging, telemetry analysis |
| `code-debug` | Programming patterns, build issues, test failures |
| `architecture` | Cross-repo docs, platform design, workflow setup |
| `deployment` | Docker, Kubernetes, compose, CI/CD |
| `supply-chain` | Image signing, SBOMs, attestation |

## Session Logs

Episodic memory (what happened in each session) lives in `sessions/`.
See `sessions/README.md` for the schema.
