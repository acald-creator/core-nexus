# Factory AI: Secure Coding / Review Agents

## Status

Accepted

## Context

Nexus needs AI-assisted **secure coding** and **code review** without conflating
that work with:

- **kiln** — hermetic, content-addressed task/build execution (Linux namespace
  isolation around pipeline targets), not an agent IDE or coding workspace
  ([nebucloud/kiln](https://github.com/nebucloud/kiln))
- **ssf** — sign / attest / SBOM / policy on build outputs (ADR 0004)
- **`platform/ai-inference`** — SOC alert triage enrichment
- **`athena-agents`** — red-range OPAR stimulation/emulation

A prior sketch wrongly treated kiln “sandbox” as the coding-agent workspace.
kiln’s sandbox is build hermeticity only. Agents need their own runtime and
must **call** kiln for verify/build steps.

## Decision

### Ownership and placement

| Concern | Default |
| --- | --- |
| Factory AI agents | Sibling repo **`nebucloud/factory-agents`** (name may refine; org = nebucloud) |
| Hermetic verify/build | **kiln** (callee of agents / CI — never redefined as agent runtime) |
| Sign / attest / SBOM | **nebucloud/ssf** (ADR 0004) |
| Non-AI SAST / secrets / PR enforce | **security-compliance-hub** |
| Human UX for high-risk | Nexus Console Approvals (+ audit) via gateway/MCP |
| SOC triage models | `platform/ai-inference` only — do not host coding LLMs there |

Do **not** implement factory coding/review agents inside `core-nexus` platform
services except thin gateway/MCP/Console wiring. Do **not** point Athena red
skill packs at product repos.

### Product order

1. **Review agent first** — PR/diff in → findings + risk + optional suggested
   patch; never merges.
2. **Coding agent second** — same runtime and safety pattern; allowlisted paths;
   bot opens PRs only; merge remains human.
3. Shared runtime uses **OPAR-style** observe/plan/act/reflect with allowlists and
   capability gates (patterns from `athena-agents`, not adversary skills).

### Triggers and gates

- **Primary trigger:** GitHub App / check run on pull request.
- **Human gate:** required for merge and for applying high-risk suggested fixes;
  Console Approvals is the Nexus-side surface; GitHub remains source of truth for
  PR state.
- **Autonomous merge or promote is out of scope.** Same spine rule as SOC
  response: human approval first.

### Trust chain (unchanged order)

```
agent runtime (review/coding)
  → security-compliance-hub (enforce)
  → kiln (hermetic lint/test/build on SHA)
  → ssf (sign / attest / SBOM / policy)
  → registry → Flux ImagePolicy → Argo sync
```

### Agent isolation (near-term vs later)

| Horizon | Isolation |
| --- | --- |
| Near-term | Ephemeral CI Job / k8s Job: read-only checkout (or bot branch only), no cluster-admin, no push to protected defaults |
| Later | Hardened runtime (e.g. gVisor) if host isolation requires it — still **not** kiln’s build-target namespaces |
| Optional later | Edge/ephemeral runners (e.g. Cloudflare Sandbox) adjacent to R2/D1 — not required for first review agent |

### Phased delivery (factory AI)

| Phase | Intent |
| --- | --- |
| F0 | This ADR + vocabulary in collaboration docs |
| F1 | kiln verify pipelines on PR SHA (no LLM) — **started** in [`nebucloud/factory-agents`](https://github.com/nebucloud/factory-agents) (`kiln-verify` / schema) |
| F2 | Review agent + hub enforce + human gate — **started** (heuristics + Check Run JSON; GitHub App POST next) |
| F3 | Coding agent (allowlisted paths, bot PRs) |
| F4 | Signed model promote via purple workbench (arch 06/07) |

## Consequences

- Docs and agents treat **factory AI** as a factory-plane adjunct, not a fourth
  product spine plane and not a red-range capability.
- kiln remains “hermetic build engine”; wording that calls kiln a coding sandbox
  is incorrect and should be corrected when found.
- `platform/ai-inference` stays triage-only; new model serving for coding/review
  is a separate workload if/when needed.
- Creating `nebucloud/factory-agents` (or renamed equivalent) is the
  implementation home; core-nexus adds integration narrative, gateway/MCP hooks,
  and Console Approvals wiring only.
- Sibling repo: [`nebucloud/factory-agents`](https://github.com/nebucloud/factory-agents)
  (scaffold: review CLI + safety gates; F1 kiln verify and F2 LLM next).
- Follow-on may add gateway/MCP/Console Approvals wiring in core-nexus once
  the GitHub App check path is live.

## References

- ADR 0002 (spine), 0004 (ssf + kiln)
- [nebucloud/kiln](https://github.com/nebucloud/kiln) README — hermetic task execution
- [nebucloud/ssf](https://github.com/nebucloud/ssf) — “ssf does not run builds; kiln runs builds”
- `athena-agents` — OPAR / allowlist patterns (safety reuse only)
- Canvas sketch: secure-coding-kiln-ai (session artifact; ADR is source of truth)
