---
name: Cross-Repo Architecture Documentation Update
description: Pattern for propagating architecture changes across multiple Underground Nexus repositories while maintaining consistency
tags: [architecture, documentation, cross-repo, workflow]
inclusion: manual
---

## When to Apply
- A new architectural concept needs to be documented across multiple repos
- An existing feature (like LLM agents) needs to be connected to the architecture narrative
- Adding a new component, workflow, or integration that spans core-nexus + satellite repos
- Vocabulary or non-negotiable decisions need updating after a design evolution

## Approach
1. Use context-gatherer to survey existing documentation state across all relevant repos before making changes
2. Identify the gap: what exists vs what's needed (build a table of topic vs coverage vs gap)
3. Start with the deepest technical doc (e.g., `11-ai-native-integration-principles.md`) — add the detailed section here
4. Update the evolution/roadmap doc (e.g., `08-athena-adversary-fuzzer.md`) — connect phases to the new concept
5. Update the collaboration guide (`00-ai-collaboration.md`) — vocabulary, model roles, non-negotiable decisions, cross-repo table
6. Update satellite repo architecture docs (e.g., `nexus-athena/architecture.md`) — add integration section with execution context
7. Commit per-repo with descriptive messages summarizing what sections were added/modified
8. Verify no terminology drift: new vocabulary should be consistent across all touched files

## Key Patterns
- New sections get inserted at appropriate positions (not appended) — renumber subsequent sections
- Cross-references use relative paths and section numbers: "See Section 4 in doc X"
- Mermaid diagrams for integration flows (keep them simple: 3-4 nodes per subgraph)
- Tables for execution modes, profiles, components — scannable and comparable
- Vocabulary entries follow pattern: `**Term:** Definition. Additional context sentence.`
- Non-negotiable decisions are imperative statements, not suggestions
- Cross-repo context tables: repo | role | key artifacts

## Pitfalls
- Don't update docs in isolation — if you add a concept to one doc, check all related docs for consistency
- Don't forget to renumber sections after inserting new ones mid-document
- When replacing section content, verify the old content isn't duplicated (search for heading text)
- Commit satellite repos separately from core-nexus (different git histories)
- Don't overwrite existing content that's still valid — extend and connect rather than replace

## References
- `core-nexus/docs/00-ai-collaboration.md` — canonical collaboration guide (vocabulary, decisions, roles)
- `core-nexus/docs/architecture/` — numbered architecture docs (lower = more practical, higher = more aspirational)
- `nexus-athena/architecture.md` — Athena container architecture
- `core-nexus/docs/00-doc-index.md` — document index (check if new docs need listing)
- Pattern: context-gatherer first → identify gaps → deepest doc first → propagate outward
