# ADR-002: LLM Provider

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

The agent needs a large language model for:
1. Multi-turn conversation and profile extraction
2. Investment reasoning and suggestion generation
3. Text embedding generation for vector memory

The project mandate is Azure-first. We evaluate whether to use Azure OpenAI Service or alternative providers.

---

## Options Considered

### Option A — Azure OpenAI Service (GPT-4o + text-embedding-3-small)

Microsoft's managed deployment of OpenAI models within Azure data centres. Data does not leave
the Azure tenant; subject to Azure's data processing agreements.

**Pros:**
- Data residency within Azure — critical for regulated workloads and a strong showcase differentiator
- Private endpoint support — traffic never traverses the public internet
- Azure RBAC and Managed Identity access (no API key required in production)
- SLA-backed (99.9 % uptime)
- Integrated with Azure Monitor for token usage and cost tracking
- Semantic Kernel Azure OpenAI connector is first-party — zero integration friction
- GPT-4o: strong instruction-following, tool-use, and financial reasoning
- `text-embedding-3-small`: cost-efficient, 1536 dimensions, high quality

**Cons:**
- Regional availability of models varies; need to check quota in target region
- Provisioned throughput (PTU) required for high-load production; pay-per-call (S0) fine for showcase
- Slightly higher latency than direct OpenAI API due to Azure routing

---

### Option B — OpenAI API (direct)

Using OpenAI's public API from within Azure-hosted compute.

**Pros:**
- Access to latest model versions immediately (no Azure deployment lag)
- Simpler setup for prototyping

**Cons:**
- Data leaves Azure tenant — violates data residency goal
- No Azure RBAC integration; API key management is external
- Not an Azure service — weakens the "all-Azure" showcase narrative
- No Azure billing integration

---

### Option C — Azure AI Services (phi-4 / open-source models via Azure AI Foundry)

Deploying open-weight models (Phi-4, Llama 3, Mistral) via Azure AI Foundry serverless endpoints.

**Pros:**
- No per-token OpenAI licensing cost at scale
- Models fully within Azure control plane

**Cons:**
- Open-weight models significantly weaker than GPT-4o on financial reasoning and instruction-following
- Tool/function-calling support is inconsistent across models
- Operational complexity: model serving, scaling, GPU quota
- Embedding quality from open models lags `text-embedding-3-small`

---

## Decision

**Azure OpenAI Service — GPT-4o for chat, text-embedding-3-small for embeddings (Option A)**

---

## Rationale

Azure OpenAI is the unambiguous choice for an Azure-first showcase. It delivers enterprise data
residency, Managed Identity auth, and SLA guarantees while providing the strongest model quality
for financial dialogue and tool use. The Semantic Kernel Azure OpenAI connector makes integration
trivial. Direct OpenAI API undermines the Azure story; open-weight models cannot match GPT-4o
quality for this use case.

`text-embedding-3-small` is chosen over `text-embedding-3-large` for cost efficiency;
1536-dimension vectors are sufficient for user profile retrieval with a small corpus.

---

## Consequences

- **Positive:** All data stays within the Azure tenant — strong compliance posture.
- **Positive:** Managed Identity auth eliminates API key rotation risk.
- **Positive:** Azure Monitor gives out-of-the-box token cost dashboards.
- **Negative:** Azure OpenAI model rollout lags OpenAI by days to weeks; new model features may not be immediately available.
- **Risk:** Regional model quota limits could throttle the showcase under high load.
- **Mitigation:** Request quota increase in advance; set `max_tokens` conservatively; implement exponential backoff on 429 responses.
