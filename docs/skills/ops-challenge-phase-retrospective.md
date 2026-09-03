---
name: Challenge Phase Retrospective
description: Close a 100 Days calendar phase — metrics, honest gaps, roadmap note, changelog share
tags: [ops, documentation, 100-days, roadmap]
inclusion: manual
---

## When to Apply
- Days 20 / 40 / 60 / 80 / 98–100 style retrospectives
- Closing a challenge calendar bucket without claiming architecture phase exit

## Approach
1. Separate **challenge Phase N** (day range) from **architecture Phase N** (`docs/architecture/03`).
2. Update tracking metrics with measured numbers only — mark unknowns as `—`.
3. Touch the architecture roadmap only for exit criteria you can evidence; add a dated calendar-close note.
4. Publish changelog on acaldwell.dev; link it from the roadmap note.
5. List the next three concrete moves — not a full Phase rewrite.

## Key Patterns
- Progress log row + checkbox in `docs/100-days-challenge.md`
- Roadmap: checked Suricata hybrid-sensor; SBOM/attest stays open until CI is routine
- Honest gaps: capture path, Day 9 bridge, Property 8, coverage %

## Pitfalls
- Do not mark architecture Phase 1 “complete” when only the calendar bucket closed
- Do not invent detection coverage from triage POSTs alone
- Do not bury deferred Builds — carry them into the next phase list

## References
- `docs/100-days-challenge.md`
- `docs/architecture/03-phased-implementation-roadmap.md`
- `/nexus/changelog` on acaldwell.dev
