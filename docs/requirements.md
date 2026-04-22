# Investment Coach Agent — Requirements

## 1. Overview

A conversational AI investment coach that profiles users through natural dialogue and provides
personalised investment guidance. Built entirely on Azure to demonstrate enterprise-grade
cloud AI capabilities.

---

## 2. Functional Requirements

### 2.1 Onboarding & User Profiling

| ID | Requirement |
|----|-------------|
| FR-01 | Agent greets new users and initiates a structured profiling conversation |
| FR-02 | Agent collects: age, income range, risk tolerance, investment goals, time horizon, and existing assets |
| FR-03 | Agent accepts free-form answers and extracts structured profile fields using LLM |
| FR-04 | Profile is persisted to long-term memory after each turn so it survives session restarts |
| FR-05 | Agent detects returning users and recalls their profile without re-asking answered questions |
| FR-06 | Profile updates incrementally — new information shared mid-conversation is merged, not replaced |

### 2.2 Investment Guidance

| ID | Requirement |
|----|-------------|
| FR-07 | Agent answers investment questions grounded in the user's stored profile |
| FR-08 | Agent suggests asset classes, allocation strategies, and instruments appropriate to the profile |
| FR-09 | Agent explains the reasoning behind each suggestion in plain language |
| FR-10 | Agent declines to give specific stock picks or guarantee returns; includes a regulatory disclaimer |
| FR-11 | Agent can handle follow-up clarifications and refine prior suggestions within the same session |

### 2.3 Conversation Management

| ID | Requirement |
|----|-------------|
| FR-12 | Short-term chat history (last N turns) is maintained per session to support coherent dialogue |
| FR-13 | Long-term profile memory is retrieved semantically, not just by user ID |
| FR-14 | Agent gracefully handles off-topic queries by redirecting to investment topics |
| FR-15 | Conversation history is accessible to authorised users for audit purposes |

### 2.4 Administration & Observability

| ID | Requirement |
|----|-------------|
| FR-16 | All LLM calls, token counts, and latencies are logged |
| FR-17 | Profile data is queryable by user ID for support/admin purposes |
| FR-18 | System exposes a health endpoint |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-01 | End-to-end response latency (user message → streamed first token) < 2 s at p95 |
| NFR-02 | Profile retrieval from vector store < 200 ms at p99 |
| NFR-03 | System handles 50 concurrent sessions without degradation |

### 3.2 Security

| ID | Requirement |
|----|-------------|
| NFR-04 | All secrets (API keys, connection strings) stored in Azure Key Vault; no secrets in code or env files |
| NFR-05 | User profile data encrypted at rest and in transit |
| NFR-06 | Authentication via Azure Entra ID (formerly AAD); no anonymous access to the API |
| NFR-07 | PII in profiles is tagged and subject to data-retention policies |

### 3.3 Reliability & Scalability

| ID | Requirement |
|----|-------------|
| NFR-08 | Service availability ≥ 99.5 % monthly |
| NFR-09 | Stateless API layer — horizontal scaling with no session affinity required |
| NFR-10 | Graceful degradation if vector store is unavailable (fall back to session-only context) |

### 3.4 Compliance

| ID | Requirement |
|----|-------------|
| NFR-11 | System must display a financial disclaimer on every investment suggestion |
| NFR-12 | Audit log retained for 90 days minimum |
| NFR-13 | User can request deletion of their profile (right to erasure) |

### 3.5 Developer Experience

| ID | Requirement |
|----|-------------|
| NFR-14 | Infrastructure defined as code (Bicep) |
| NFR-15 | Local development possible with Azure emulators / free-tier resources |
| NFR-16 | CI/CD pipeline via GitHub Actions → Azure |

---

## 4. Assumptions & Constraints

- Target environment: Azure commercial cloud (no sovereign / government cloud constraints initially)
- Budget: dev/test tier — cost-optimised service SKUs acceptable for the showcase
- Regulatory scope: informational guidance only, not regulated financial advice; standard disclaimer sufficient
- Users authenticated externally; this system receives a validated JWT bearing a `user_id` claim
- No real-time market data feed in v1 — agent reasons from general financial knowledge in the LLM
