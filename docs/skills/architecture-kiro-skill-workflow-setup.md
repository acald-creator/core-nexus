---
name: Kiro Auto Skill Generation Workflow Setup
description: Pattern for building Hermes Agent-style auto skill generation and persistent memory in Kiro
tags: [architecture, kiro, workflow, skills, automation]
inclusion: manual
---

## When to Apply
- Setting up a new Kiro workspace for skill-driven development
- Adding auto-skill-generation to a new repository
- Onboarding a new domain into the skill library
- Replicating the "solve once, remember forever" pattern in a fresh environment

## Approach
1. Create the auto-skill-gen hook (`.kiro/hooks/auto-skill-gen.json`) with `Stop` trigger and `agent` action type
2. Create seed skills at `~/.kiro/skills/` for each known domain — these bootstrap the system so it doesn't start cold
3. Create a user-level steering file (`~/.kiro/steering/skill-driven-workflow.md`) with `inclusion: auto` that instructs the agent to check skills before work and generate after novel work
4. Create workspace-level steering (`<repo>/.kiro/steering/`) pointing to relevant skills per repo
5. Place the hook in each workspace's `.kiro/hooks/` directory (hooks are workspace-scoped, not user-scoped)
6. Verify the full layout: hooks in each repo, steering at both levels, skills at user level

## Key Patterns
- Hook trigger: `Stop` — fires when session completes, perfect for retrospective skill capture
- Hook action: `agent` — injects a prompt into context rather than running a shell command
- Skills use `inclusion: manual` so they don't all load every session (reference with `#` in chat)
- Steering uses `inclusion: auto` so it loads every session without user action
- Skills are user-level (`~/.kiro/skills/`) for cross-repo reuse
- Workspace steering points to which skills are relevant for that specific repo
- Skill format: front matter (name/description/tags) + sections (When to Apply, Approach, Key Patterns, Pitfalls, References)

## Pitfalls
- `createHook` resolves to the first workspace root in multi-root workspaces — manually copy hook JSON to other repos
- Don't make skills `inclusion: auto` — they'll all load every session and waste context
- Don't put skills at workspace level unless they're truly repo-specific — user-level is better for cross-repo memory
- The Stop hook fires twice in multi-root workspaces if both have the hook — the prompt deduplicates but check for double writes
- Keep individual skills focused (one domain each) rather than one mega-skill

## References
- `~/.kiro/steering/skill-driven-workflow.md` — the auto-inclusion steering that drives the workflow
- `~/.kiro/skills/` — user-level skill library
- `<repo>/.kiro/hooks/auto-skill-gen.json` — the Stop hook (per workspace)
- `<repo>/.kiro/steering/` — workspace-specific context pointing to relevant skills
- Hermes Agent by Nous Research — the inspiration pattern (auto skill generation + Honcho memory)
- hakluke's approach: "build capability as a tool + skill, save tokens on repeat encounters"
