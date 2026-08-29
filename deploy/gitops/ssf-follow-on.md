# SSF follow-on (after core-nexus Flux/Argo sketch)

Work lands in [`nebucloud/ssf`](https://github.com/nebucloud/ssf) + [`nebucloud/kiln`](https://github.com/nebucloud/kiln).
Do not duplicate Cosign/SBOM tooling inside core-nexus.

## Goal

Publish **signed OCI images** for Nexus workloads so Flux ImagePolicy can pin
semver (or digest) and Argo can sync `deploy/kubernetes/soc/overlays/gitops-lab`.

```
kiln build nexus-console
  → ssf run ssf.yaml          # sign + sbom + attest + policy (needs OCI type)
  → push phoenixvlabs/nexus-console:vX.Y.Z
  → Flux ImageRepository sees tag
  → ImageUpdateAutomation commits pin
  → Argo syncs Deployment
```

## Gaps in ssf today (HEAD ~2.4d)

| Need for this loop | Status |
|--------------------|--------|
| Artifact type `oci` | Missing (binary only) |
| `ssf sign` / `verify` for registry refs | Needs OCI |
| `ssf.yaml` sample for container image | Add under nexus image repos or ssf/testdata |
| Semver tags on publish | Process / CI convention |
| Vault/Fulcio keyless | Later; file or vault:// OK for lab |
| Flux/Argo awareness | Not required inside ssf |

## Suggested ssf work order

1. **Implement `pkg/artifact/oci.go`** — resolve registry reference → manifest digest; wire Cosign `sign`/`verify`/`attest` for OCI.
2. **testdata `sample-oci.ssf.yaml`** — `type: oci`, reference `phoenixvlabs/nexus-console:${VERSION}`.
3. **Policy** — ensure `policies/base.cue` accepts OCI metadata (digest, repo).
4. **CI job (ssf or core-nexus)** — after image build: `ssf run` then `docker push` / `crane push` of signed tag.
5. **Handshake test** — push `v0.1.0`, confirm Flux ImagePolicy selects it, automation PR/commit updates gitops-lab markers, Argo rolls Deployment.

## Out of scope for first ssf pass

- Hyperledger / old `secure-software-factory` monorepo
- Tekton generators (optional later: `ssf tekton generate`)
- Replacing Argo with Flux Kustomization sync

## Handshake checklist

- [ ] `ssf sign` works on an OCI image in a lab registry
- [ ] Image tagged `v0.1.0` (not only `latest`)
- [ ] Flux `ImagePolicy/nexus-console` shows that version
- [ ] Git shows Flux commit under `overlays/gitops-lab`
- [ ] Argo Application `nexus-gitops-lab` Healthy + Synced
