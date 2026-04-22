# ADR-006: Programming Language & SDK

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

Choosing the primary language and SDK set determines developer ergonomics, library availability,
container image size, and long-term maintainability. Semantic Kernel (chosen in ADR-001) supports
both Python and C#.

---

## Options Considered

### Option A — Python 3.12 + Semantic Kernel Python SDK

**Pros:**
- Python is the dominant language in AI/ML; broadest ecosystem of AI libraries
- Semantic Kernel Python SDK is actively maintained and feature-parity is converging with C#
- FastAPI (async ASGI) is the de-facto standard for Python ML APIs: high performance, auto-generated OpenAPI docs, native SSE support
- `azure-identity`, `azure-search-documents`, `azure-cosmos` SDKs are all first-class
- Fastest iteration speed for prompt engineering and plugin development
- Wider developer pool for AI projects

**Cons:**
- Semantic Kernel C# SDK slightly more feature-complete (SK was C#-first)
- Python GIL limits true CPU parallelism (not an issue for I/O-bound LLM workloads)
- Container image size larger than .NET single-file publish

---

### Option B — C# (.NET 8) + Semantic Kernel C# SDK

**Pros:**
- Semantic Kernel C# SDK is the primary/reference implementation — all new features land here first
- .NET 8 has excellent performance and small Docker images (alpine-based)
- Strong Azure SDK integration across all services
- ASP.NET Core minimal API with SSE support

**Cons:**
- Smaller AI/ML ecosystem; fewer Python-native libraries (e.g. for future embedding fine-tuning)
- Longer iteration cycle for prompt experimentation vs Python notebooks
- Less common skill set in AI-focused teams

---

## Decision

**Python 3.12 + Semantic Kernel Python SDK (Option A)**

---

## Rationale

Python is the standard language for AI agent development. The Semantic Kernel Python SDK covers all
required features (Plugins, ChatHistory, Azure OpenAI connector, AI Search memory connector). FastAPI
provides production-grade async HTTP with native SSE streaming. The developer experience for prompt
iteration and plugin development is superior in Python. The C# SDK's feature lead is narrowing and
does not offset the ecosystem and productivity advantages of Python for this use case.

---

## Consequences

- **Positive:** Fastest time-to-working-agent; rich ecosystem for future enhancements.
- **Positive:** Same language as most Azure AI documentation examples — easier onboarding.
- **Negative:** Must monitor SK Python SDK changelog for feature lag relative to C# reference implementation.
- **Risk:** Python startup time in containers slightly slower than .NET.
- **Mitigation:** Use `python:3.12-slim` base image; pre-load SK kernel at startup rather than per-request.

---

## Key Dependencies (pinned)

| Package | Version | Purpose |
|---------|---------|---------|
| `semantic-kernel` | `~=1.x` | Agent orchestration, plugins |
| `fastapi` | `~=0.115` | API framework |
| `uvicorn[standard]` | `~=0.30` | ASGI server |
| `azure-identity` | `~=1.19` | Managed Identity / Key Vault auth |
| `azure-search-documents` | `~=11.6` | AI Search client |
| `azure-cosmos` | `~=4.7` | Cosmos DB client |
| `opentelemetry-sdk` | `~=1.27` | Distributed tracing → App Insights |
