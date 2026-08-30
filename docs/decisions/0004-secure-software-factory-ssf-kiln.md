# Secure Software Factory: nebucloud/ssf + kiln

## Status

Accepted

## Context

Nexus needs signed, attested images for GitOps promotion. Historical references to
FRSCA / Tekton Chains and the older `nebucloud/secure-software-factory` (Hyperledger /
xDS) monorepo created pressure to reinvent Cosign/SBOM stacks inside `core-nexus`.

## Decision

| Role | Tool |
| --- | --- |
| Hermetic build | [`nebucloud/kiln`](https://github.com/nebucloud/kiln) |
| Sign / attest / SBOM / policy | [`nebucloud/ssf`](https://github.com/nebucloud/ssf) (Cosign shellouts; `ssf.yaml`) |
| Promote | Flux ImagePolicy + Argo sync |

- Do **not** stand up a second Cosign/SBOM stack in `core-nexus` unless SSF cannot
  cover the artifact type.
- The older `nebucloud/secure-software-factory` monorepo is a **separate lineage** —
  not the Nexus factory default.
- CI may call `cosign` directly when `ssf` install is unavailable; prefer `ssf`
  when the public module is reachable (`go install github.com/nebucloud/ssf/cmd/ssf@latest`).

Follow-on checklist: `deploy/gitops/ssf-follow-on.md`.
Publish workflow: `.github/workflows/publish-platform-images.yml`.

## Consequences

- Docs treat FRSCA/Tekton as historical analogy only.
- `security-compliance-hub` remains PR/scan/enforce — keep its signing story
  distinct from registry OCI signing via SSF/Cosign.
- Factory trust is not placed in desktop webtop images.
