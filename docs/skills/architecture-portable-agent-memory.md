---
name: Portable Agent Memory Architecture
description: Design pattern for persistent agent memory that works across Kiro, Claude Code, Codex, Hermes Agent, and headless OPAR loops
tags: [architecture, workflow, memory, multi-tool, agents]
inclusion: manual
---

## When to Apply
- Designing agent workflows that need to persist knowledge across sessions
- Working across multiple AI tools (Kiro, Claude Code, Codex CLI, Hermes Agent)
- Setting up memory for headless athena-agents OPAR loop
- Deciding where to store skills, session logs, or embeddings
- Evaluating Honcho or similar memory services for the platform

## Approach
1. Identify the three memory layers needed:
   - **Skill files** (structured "how I solved it") — Markdown with front matter
   - **Session logs** (episodic "what happened") — JSONL with task/outcome/tokens
   - **Vector memory** (semantic "what's similar") — embeddings for RAG retrieval
2. Choose storage backend based on maturity:
   - Option A (simplest): Git repo directory (e.g., `core-nexus/docs/skills/`)
   - Option B (headless): MinIO bucket (`nexus-memory/skills/`, `nexus-memory/sessions/`)
   - Option C (richest): Memory service like Honcho with semantic search API
3. Wire each tool to read and write:
   - Kiro: `~/.kiro/skills/` + Stop hook for auto-generation
   - Claude Code / Codex: `CLAUDE.md` / `AGENTS.md` reference skill directory
   - athena-agents: Plan phase loads from MinIO, Reflect phase writes back
   - Any LLM via API: wrapper script injects skills into system prompt
4. Start with git-based, graduate to MinIO when headless agents run, add Honcho when multi-user

## Key Patterns
- Skill format: Markdown with YAML front matter (name, description, tags, inclusion)
- Session log format: JSONL with fields: session_id, timestamp, agent, domain, task, approach, outcome, skill_generated, files_modified, tokens_spent
- Storage hierarchy: `nexus-memory/skills/`, `nexus-memory/sessions/`, `nexus-memory/vectors/`
- Tool consumption: system prompt injection (skills) + RAG query (vector) + episodic context (session log)
- Sync pattern: `~/.kiro/skills/` ↔ `core-nexus/docs/skills/` ↔ MinIO `nexus-memory/skills/`

## Pitfalls
- Don't couple memory to a single tool (Kiro-only skills break when using Claude Code)
- Don't skip structured format — free-text notes aren't queryable for RAG
- Don't embed everything — skills and session summaries are enough for semantic search; raw code isn't useful
- Don't run Honcho before you need multi-user isolation — git + MinIO covers single-operator well
- Git-based skills need periodic curation (merge overlapping skills, prune stale ones)
- MinIO skills need versioning/signing before use in unattended agent scenarios

## References
- Hermes Agent by Nous Research — auto skill generation + persistent memory
- Honcho by Plastic Labs — AI memory service (episodic + semantic)
- hakluke's approach: "build capability as a tool + skill, save tokens on repeat encounters"
- `~/.kiro/skills/` — Kiro user-level skill files
- `~/.kiro/steering/skill-driven-workflow.md` — auto-inclusion steering for skill-driven work
- `core-nexus/docs/architecture/11-ai-native-integration-principles.md` Section 3 — vector memory (RAG)
- `core-nexus/docs/architecture/11-ai-native-integration-principles.md` Section 4 — skill persistence in OPAR
- MinIO in architecture: artifact store for datasets, skills, and evidence
