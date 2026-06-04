# AI-Native Integration Principles

**Status:** Proposed / Draft
**Context:** This document outlines the architectural shift from "bolted-on AI" (where AI is treated as an external chat widget) to an "AI-native" environment within the Underground Nexus. These principles are inspired by the Odysseus self-hosted workspace model and adapted for a secure, Kubernetes-based security lab and SOC environment.

## 1. Cookbook Architecture (Hardware-Aware AI Inference)

The inference layer (`platform/ai-inference`) must be deeply aware of the hardware it runs on. Rather than relying on static deployment configurations, the Nexus should dynamically adapt to available resources.

### Key Concepts

- **Pre-flight Hardware Scanning**: Inference pods use init-containers or DaemonSets to scan the underlying node for GPU availability (e.g., checking for CUDA, ROCm, or Metal).
- **Dynamic Serving Engine Selection**:
  - **High-Tier (NVIDIA/AMD GPUs)**: Deploy `vLLM` serving highly optimized formats like FP8 or AWQ for maximum throughput.
  - **Low-Tier (CPU-only / Edge)**: Fallback to `llama.cpp` serving highly quantized GGUF models.
- **Automated Model Provisioning**: The "Cookbook" acts as an internal model registry (backed by MinIO). When the lab bootstraps, it pulls the appropriate model size based on the hardware scan, ensuring the lab is immediately functional without manual tuning.

## 2. Agentic Workspace (MCP)

The user interface (`platform/workbench`) is not just a terminal and a browser; it is an intelligent agentic client powered by the Model Context Protocol (MCP).

### Key Concepts

- **Workbench as an MCP Client**: The analyst's desktop environment natively connects to a local LLM and orchestrates tools.
- **Infrastructure as Tools**: Every major component in the lab is exposed via MCP Servers:
  - **Wazuh MCP Server**: Allows the agent to query logs and pull alerts.
  - **MinIO MCP Server**: Allows the agent to read and write PCAPs, artifacts, and reports.
  - **k3d / Kubernetes MCP Server**: Allows the agent to spin up adversary emulation pods in the `Athena` environment automatically.
- **"Assisted, Not Delegated" UX**: The analyst drives the investigation. The AI provides inline ghost-text for complex Suricata rules, highlights anomalies directly in logs, and auto-completes incident reports in the editor, rather than forcing the user to switch context to a separate chat window.

## 3. AI-Native Triage Layer (SOC)

In a traditional SOC, human analysts review raw event streams. In an AI-native SOC (`platform/soc`), the AI serves as the front-line triage agent, processing data before a human ever sees it.

### Key Concepts

- **Continuous Inference Loop**: High-fidelity alerts from Suricata and Wazuh are streamed directly into the local inference engine.
- **Automated Enrichment**:
  - **Auto-Tagging**: The AI assigns urgency and categorizes the threat.
  - **Auto-Summarization**: Raw JSON event logs are translated into human-readable attack narratives.
  - **Mitigation Drafting**: The AI preemptively drafts Kubernetes Network Policies or firewall rules to block the threat, awaiting human approval.
- **Persistent Vector Memory**: 
  - Using a vector database (e.g., ChromaDB or Milvus), every analyzed event, incident report, and executed command is embedded into a semantic memory store.
  - When a new event occurs, the AI performs a RAG (Retrieval-Augmented Generation) query to pull context from similar past incidents, allowing the agent's knowledge to compound and evolve over time.

## 4. Multi-Project Security & Orchestration Layer

Underground Nexus does not function solely as an isolated security workspace. It acts as an integration and orchestration layer across external projects and development targets.

### Key Concepts

- **Cross-Boundary Telemetry Ingestion**: The AI-SOC inference layer (`platform/ai-inference`) is exposed via secure gRPC/HTTPS interfaces to ingest telemetry (logs, network flows, process events) from other projects running outside the local namespace or cluster.
- **Universal MCP Interface**: By exposing the Nexus workspace as an MCP Server gateway, external LLM agents and workflows in other projects can access the tools and security context hosted in the Nexus (e.g., executing fuzzer runs, retrieving analysis reports, querying indexed security states).
- **Federated Attestation & Policy Enforcer**: The secure build pipelines and secrets boundaries within the Nexus secure software factory can broker trust and attestations for external software bundles, creating a centralized security assurance service for your entire project ecosystem.
