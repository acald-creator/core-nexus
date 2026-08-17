# Claude Instructions

Use `docs/00-ai-collaboration.md` as the canonical architecture and collaboration guide.

## Strengths for This Repo

- Architecture critique and structural consistency review.
- Threat modeling LLM agent workflows (OPAR safety controls, allowlist integrity, capability gates).
- Security claim review — flag unsupported "tamper-proof" or "zero-day" assertions.
- Narrative consistency across numbered architecture docs.
- Finding ambiguous assumptions about phase boundaries (Phase 1 vs 2 vs 3).
- Reviewing whether stimulation/emulation documentation overstates autonomy guarantees.

## Output Expectations

- Return discrepancies with file and section references.
- Avoid rewriting architecture unless explicitly asked.
- When reviewing agent-related docs, verify safety controls are documented for every autonomous action path.
- Flag any place where ground-truth labels could be poisoned or skills could introduce unsafe patterns.
