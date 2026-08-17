# Gemini Instructions

Use `docs/00-ai-collaboration.md` as the canonical architecture and collaboration guide.

## Strengths for This Repo

- Research synthesis on LLM serving engines (vLLM, Ollama, llama.cpp) and model selection.
- Comparing platform and deployment options (Kubernetes, UDS/Zarf, bare-metal).
- Producing tradeoff tables for agent memory backends (vector DBs, skill persistence, Honcho-style memory).
- Checking external ecosystem assumptions for MCP, inference hardware, and container runtimes.
- Evaluating adversary emulation frameworks and MITRE ATT&CK coverage tooling.

## Output Expectations

- Cite sources and distinguish current facts from assumptions or future design ideas.
- When evaluating LLM backends, include context window size, token throughput, and resource requirements.
- When comparing agent memory approaches, note persistence model, query latency, and cross-session behavior.
