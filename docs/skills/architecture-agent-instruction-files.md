---
name: Multi-Model Agent Instruction File Management
description: Pattern for maintaining AGENTS.md, CLAUDE.md, and GEMINI.md across Underground Nexus repositories
tags: [architecture, documentation, multi-model, workflow]
inclusion: manual
---

## When to Apply
- Revising agent instruction files after architecture changes
- Adding a new repository to the Underground Nexus ecosystem
- Updating model-specific guidance after adding new capabilities (e.g., LLM agents)
- Onboarding a new AI model to the collaboration workflow

## Approach
1. Read all agent files across all repos first (`find <repos> -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "GEMINI.md"`)
2. Identify what's changed in architecture that needs to propagate (new components, workflows, vocabulary, cross-repo relationships)
3. Update each file type with its specific purpose:
   - **AGENTS.md**: Repo role, key references, agent expectations, cross-repo table, guardrails, build/test commands (if applicable)
   - **CLAUDE.md**: Review strengths specific to this repo, security/credential touchpoints, output format expectations
   - **GEMINI.md**: Research strengths, version pins, standing research questions, evaluation criteria
4. Ensure consistency: cross-repo tables should be reciprocal (if A references B, B should reference A)
5. Commit per-repo with descriptive messages

## Key Patterns
- AGENTS.md structure: Repo Role → Key References → Agent Expectations → Cross-Repo Context table → Guardrails
- CLAUDE.md structure: Strengths for This Repo → (optional: credential locations, file-to-concern mapping) → Output Expectations
- GEMINI.md structure: Strengths for This Repo → (optional: version pins, research questions) → Output Expectations
- Cross-repo table format: `| Repository | Relationship |`
- Skill references: "Check `~/.kiro/skills/` for applicable skills (especially `<specific-skill>.md`)"
- Guardrails are imperative statements, not suggestions

## Pitfalls
- Don't put full file layouts in AGENTS.md if they're already in architecture.md (causes maintenance drift)
- Don't duplicate build commands if they're documented elsewhere — include only the most common ones
- Ensure cross-repo tables are symmetric across repos
- When nexus-webtop-soc AGENTS.md was too long (139 lines of file layout + env vars + commands), it became hard to maintain — keep concise, point to architecture.md for details
- Commit each repo separately (different git histories)

## References
- `<repo>/AGENTS.md` — Codex/Kiro primary instruction file
- `<repo>/CLAUDE.md` — Claude-specific review guidance
- `<repo>/GEMINI.md` — Gemini-specific research guidance
- `core-nexus/docs/00-ai-collaboration.md` Section 2 — canonical model roles definition
- Pattern: read all → identify delta → update per file type → ensure reciprocal cross-refs → commit per-repo
