# Shared LLM Serving Plane (kvcached on GPU)

## Status

Proposed

## Context

Several Nexus workloads need LLM inference, but none should embed a GPU serving
engine inside application logic:

| Workload | Repo / component | LLM need | Today |
| --- | --- | --- | --- |
| SOC triage enrichment | `platform/ai-inference` | Optional future LLM summarization / RAG | NumPy baseline v1.1.0 — **no LLM runtime** |
| Red-range OPAR | `athena-agents` | Planning / technique selection | HTTP client to Ollama, vLLM, or llama.cpp |
| Factory review / coding | `nebucloud/factory-agents` (ADR 0009) | PR diff review; coding agent later | HTTP client to Ollama, OpenAI, or vLLM |
| Analyst workbench | `platform/workbench` (MCP) | Assisted investigation (draft) | Not deployed as LLM host |

ADR 0009 locks **coding LLMs out of `platform/ai-inference`**. Architecture doc
`11-ai-native-integration-principles.md` describes hardware-aware serving (vLLM on
GPU, Ollama/llama.cpp on CPU) but does not define a **shared serving tier** or how
multiple models coexist on scarce GPU memory.

[kvcached](https://github.com/ovg-project/kvcached) is an Apache 2.0 library
that virtualizes LLM KV-cache GPU memory for **vLLM** and **SGLang**. It enables
elastic, on-demand physical page mapping so multiple models can share one GPU
without static per-model VRAM reservations at startup. Red Hat’s
[Sardeenz](https://github.com/rh-aiservices-bu/sardeenz) builds on kvcached for
multi-model serving on Kubernetes/OpenShift.

Nexus lab overlays (`deploy/kubernetes/soc/overlays/r2`) do not deploy GPU
inference today. Integrating kvcached before a validated serving plane would add
operational and supply-chain risk without near-term benefit.

## Decision

### Placement: shared serving plane, not inside triage

Introduce a **shared LLM serving plane** as infrastructure distinct from
`platform/ai-inference`:

```
Callers (HTTP/OpenAI-compatible clients)
  ai-inference (optional future LLM path)
  athena-agents
  factory-agents
  workbench MCP (later)
        │
        ▼
  platform/llm-serving  (new deploy target — name may refine)
        │
        ├── dev / CPU:  Ollama or llama.cpp (standalone; no kvcached)
        └── GPU lab/prod: vLLM or SGLang (+ kvcached when multi-model)
```

- **`platform/ai-inference` remains the triage API and persistence layer.** It may
  call the serving plane; it does not load vLLM/SGLang or host coding models.
- **Factory and Athena remain clients** of the serving plane (per ADR 0009).
- **Do not embed kvcached** in ai-inference, gateway, or agent runtimes. kvcached
  is a GPU memory layer under vLLM/SGLang only.

### Engine selection by environment

| Environment | Serving engine | kvcached | Notes |
| --- | --- | --- | --- |
| Local dev (Mac / CPU) | Ollama or llama.cpp | No | Fast iteration; no CUDA requirement |
| Lab GPU node (single model) | vLLM or SGLang | Optional / off | Pin one model; static `--gpu-memory-utilization` acceptable |
| Lab GPU node (multi-model) | vLLM or SGLang | **Yes** — default when ≥2 models share one GPU | `ENABLE_KVCACHED=true`, `KVCACHED_AUTOPATCH=1` |
| Production-like GPU | Same as lab multi-model | Yes, after spike | Images via SSF sign/attest (ADR 0004); Flux ImagePolicy (ADR 0003) |

kvcached integration is **deferred** until phase L2 (below). Near-term work may
stand up a single-model vLLM or Ollama endpoint without kvcached.

### Kubernetes path (optional orchestration layer)

When multi-model routing, sleep mode, or cluster-level memory limits are required
on GPU nodes, evaluate **Sardeenz** (kvcached + k8s) before building a bespoke
controller in core-nexus. GitOps delivery follows ADR 0003 (Flux pin + Argo sync).

### Trust chain for serving images

Serving engine images (including `ghcr.io/ovg-project/kvcached-vllm` or
`-sglang` derivatives) enter the factory path:

```
pinned upstream base + kvcached
  → kiln (hermetic build/test where applicable)
  → ssf (sign / attest / SBOM)
  → registry → Flux ImagePolicy → Argo sync
```

Do not run unpinned autopatch stacks in production-like environments.

### Security and isolation

- Treat GPU inference nodes as **dedicated inference hosts**, not a substitute for
  gVisor or agent sandboxing. kvcached containers typically require large shared
  memory, `ipc=host`, and elevated privileges — acceptable on an isolated GPU
  node, not co-located with unrestricted agent tooling.
- Model weights and API keys: Vault (ADR 0008) or cluster secrets; never in git.
- Caller authentication: network policy + API key or mTLS between callers and
  serving plane; no anonymous cluster-wide access.
- OPAR / factory allowlists and human gates (ADR 0009) are unchanged — kvcached
  affects GPU scheduling only.

### Version pinning

kvcached uses **runtime autopatch** against specific vLLM/SGLang versions. Pin
engine + kvcached versions as a **single matrix row** in deploy manifests and
document upgrades in release notes. Do not float `latest` on production-like overlays.

### Phased delivery (serving plane)

| Phase | Intent | kvcached |
| --- | --- | --- |
| L0 | Current: NumPy triage; agents use external Ollama/API | — |
| L1 | Deploy `platform/llm-serving` with **one** model on GPU (or Ollama in lab) | Off |
| L2 | **Two or more models** on one GPU (e.g. triage-7B + athena-planner-8B) | On — spike validates TTFT, OOM, reclaim |
| L3 | k8s multi-model router (Sardeenz or equivalent) + sleep mode | On |
| L4 | Optional LLM path in ai-inference (summarization/RAG) as **client** of L1–L3 | Per L2/L3 |

### Spike criteria (gate before L2)

Before enabling kvcached in any GitOps overlay:

1. Reproduce mixed bursty workload (triage-like + OPAR-like request patterns) on
   one GPU with and without kvcached.
2. Record TTFT p50/p95, OOM rate, and idle reclaim latency.
3. Confirm pinned vLLM/SGLang + kvcached version pair passes kiln/ssf pipeline.
4. Document rollback: disable `ENABLE_KVCACHED` and fall back to single-model static reservation.

## Consequences

- Resolves tension between doc `11` (hardware-aware vLLM inside inference pods) and
  ADR 0009 (no coding LLMs in ai-inference): **serving moves to a shared plane**;
  ai-inference stays triage-focused.
- No kvcached work in current Phase 1 deliverables (F2 GitHub Check Run, lab
  restore, NumPy triage) until L1 serving exists.
- New deploy surface (`platform/llm-serving` or `deploy/kubernetes/.../llm-serving`)
  will be added when L1 starts; not required for this ADR acceptance.
- Ollama-only local dev remains valid; kvcached is GPU multi-model optimization, not
  a universal Nexus dependency.
- Agents and factory-agents keep OpenAI-compatible client backends; base URL points
  at the serving plane instead of ad hoc Ollama ports.
- Operational owners must monitor GPU memory via kvcached `kvtop` / `kvctl` when L2+.
- If kvcached upstream diverges from pinned vLLM releases, prefer delaying upgrade
  over running an untested autopatch pair.

## References

- ADR 0002 (spine), 0003 (GitOps), 0004 (ssf + kiln), 0009 (factory AI placement)
- `docs/architecture/11-ai-native-integration-principles.md` — Cookbook / hardware scan (future LLM path)
- `platform/ai-inference/README.md` — current NumPy baseline
- [ovg-project/kvcached](https://github.com/ovg-project/kvcached) — elastic KV cache, vLLM/SGLang integration
- [rh-aiservices-bu/sardeenz](https://github.com/rh-aiservices-bu/sardeenz) — k8s multi-model on kvcached
- [kvcached deployment docs](https://deepwiki.com/ovg-project/kvcached/6-deployment-and-configuration)
