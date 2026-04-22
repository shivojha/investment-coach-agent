# ADR-005: Deployment Platform

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

The API layer (FastAPI + Semantic Kernel) is a containerised Python application. We need a hosting
platform that:
- Runs Docker containers
- Scales horizontally (stateless workload)
- Integrates with Azure Key Vault for secrets
- Supports Managed Identity
- Is cost-effective for a showcase (not always-on at high load)
- Minimises platform operations

---

## Options Considered

### Option A — Azure Container Apps (ACA)

Serverless container hosting built on Kubernetes (KEDA), without exposing Kubernetes to the operator.

**Pros:**
- Scales to zero when idle — $0 cost between demo sessions
- Scale-out on HTTP request queue depth (KEDA HTTP scaler) — handles bursts automatically
- Built-in ingress (HTTPS), no need to configure a load balancer or API Gateway
- Managed Identity supported natively — Key Vault secrets injected as env vars or volume mounts
- Integrated with Dapr (optional) for future sidecar patterns
- No cluster to manage — ACA managed environment handles the control plane
- Log streaming and metrics natively in Azure Monitor
- Revision-based deployment — blue/green and canary built in
- VNET integration for private endpoint connectivity to AI Search and Cosmos DB

**Cons:**
- Less control than AKS for advanced networking or GPU workloads
- Cold-start latency (a few seconds) when scaling from zero — acceptable for showcase

---

### Option B — Azure Kubernetes Service (AKS)

Full managed Kubernetes cluster.

**Pros:**
- Maximum flexibility and control
- Ideal for complex multi-service architectures
- Supports GPU nodes for model inference

**Cons:**
- Significant operational overhead: cluster upgrades, node pool management, networking
- Minimum cost ~$50–150/month for a small cluster even at low load
- Overkill for a single-service API showcase
- Scaling to zero requires KEDA configuration — same capability ACA gives for free

---

### Option C — Azure App Service (Web App for Containers)

PaaS container hosting with a simpler mental model.

**Pros:**
- Very familiar to Azure practitioners
- Easy deployment via `az webapp` CLI
- Managed TLS, custom domains

**Cons:**
- Minimum always-on cost (F1 free tier is CPU-throttled — unsuitable for LLM latency requirements)
- Scale-to-zero not available on standard tiers
- Less modern than ACA for containerised workloads — ACA is the recommended path for new container apps
- No KEDA-based event-driven scaling

---

### Option D — Azure Functions (Consumption Plan)

Serverless function hosting.

**Pros:**
- True pay-per-invocation, generous free tier (1M requests/month)
- Scale-to-zero inherent

**Cons:**
- Cold-start latency is worse than ACA for a Python FastAPI process
- 230-second max execution timeout — streaming LLM responses need long-lived connections
- SSE (Server-Sent Events) streaming is not natively supported on HTTP trigger bindings
- Not a natural fit for a full ASGI application

---

## Decision

**Azure Container Apps (Option A)**

---

## Rationale

ACA is the modern, recommended Azure platform for containerised microservices. Scale-to-zero
eliminates idle cost for a showcase, KEDA-based scale-out handles bursts, and Managed Identity
integration is first-class. It requires no cluster operations, making it the right size for this
workload. AKS is over-engineered; App Service lacks scale-to-zero; Azure Functions does not
support SSE streaming required by the LLM response design.

---

## Consequences

- **Positive:** Zero idle cost — important for a showcase that runs intermittently.
- **Positive:** Revision-based deployments enable safe rollbacks with one command.
- **Positive:** VNET integration enables private connectivity to AI Search and Cosmos DB.
- **Negative:** Cold-start from zero (~2–3 s) adds latency on the first request after idle period.
- **Mitigation:** Set `minReplicas: 1` during demo windows to eliminate cold-starts; scale to 0 outside demos via a scheduled rule.
- **Risk:** ACA has a concurrent request limit per replica (default 10); tune `--max-concurrent-requests` based on observed LLM call duration.
