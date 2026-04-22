# ADR-003: Long-Term Memory / Vector Store

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

The agent stores user profiles as long-term memory. Retrieval must support:
- Exact lookup by `user_id` (returning user recognition)
- Semantic search over profile text (contextual recall)
- Fast upsert after each turn

The original design used Qdrant (open-source). We need an Azure-native or Azure-compatible replacement.

---

## Options Considered

### Option A — Azure AI Search (formerly Cognitive Search)

Azure's managed search service with hybrid vector + keyword retrieval.

**Pros:**
- Fully managed, no infrastructure to operate
- Hybrid search: BM25 keyword + HNSW vector in a single query — best retrieval quality
- Semantic ranker (optional) for re-ranking results
- Native integration with Semantic Kernel `AzureAISearchVectorStore`
- Filterable fields enable `filter=id eq 'user_id'` for O(1) exact lookup
- Free tier: 1 index, 50 MB, 3 replicas — sufficient for showcase
- Azure RBAC + private endpoint support
- Index schema supports structured profile fields alongside embedding

**Cons:**
- Basic SKU costs ~$73/month if free tier is exceeded (acceptable for production)
- Not a pure vector database — no approximate nearest-neighbour tuning beyond HNSW parameters
- Slightly more operational setup than a hosted Qdrant cloud instance

---

### Option B — Azure Cosmos DB for NoSQL with Vector Search

Cosmos DB now supports vector search (DiskANN index) in its NoSQL API.

**Pros:**
- Single store for both profile documents and chat history (simplifies topology)
- Serverless pricing — cost scales to zero when idle
- Global distribution available

**Cons:**
- Vector search in Cosmos DB is newer and less mature than Azure AI Search
- No hybrid BM25 + vector in one query — pure vector only
- DiskANN index has minimum document thresholds before quality is good
- Semantic Kernel memory connector for Cosmos DB vector is community-contributed, not first-party
- Conflating chat history and profile memory in one store couples two different access patterns

---

### Option C — Azure Database for PostgreSQL Flexible Server + pgvector

Open-source pgvector extension on Azure-managed PostgreSQL.

**Pros:**
- SQL familiarity; rich query language for profile filtering
- pgvector is battle-tested

**Cons:**
- Requires a persistent PostgreSQL instance — no serverless tier
- Not Azure-native in spirit (it's OSS on Azure); weakens the showcase narrative
- No Semantic Kernel first-party connector — requires custom implementation
- Operational overhead: backups, patching managed but still a VM-based service

---

### Option D — Qdrant on Azure Container Apps (original design)

Running the Qdrant open-source server as a container on ACA.

**Pros:**
- Exactly matches original architecture intent
- Rich vector DB features (payload filtering, named vectors, snapshots)

**Cons:**
- Requires persistent volume — Azure Files or managed disk — adding cost and ops burden
- Not a managed service; we own availability, backups, upgrades
- Weakens the "all Azure managed services" showcase goal
- Qdrant Cloud (managed) is not an Azure service

---

## Decision

**Azure AI Search (Option A)**

---

## Rationale

Azure AI Search is the most Azure-native, fully managed vector store with first-party Semantic Kernel
support. Its hybrid retrieval (vector + BM25) is superior to pure-vector alternatives for profile
recall — especially when profile text is sparse early in onboarding. The filterable `id` field
provides O(1) exact lookup for returning users without vector search overhead.

Cosmos DB vector search was attractive for topology simplicity but its vector maturity and SK
connector status do not match AI Search. Qdrant on ACA introduces self-managed infrastructure
that conflicts with the managed-services showcase goal.

---

## Consequences

- **Positive:** Best-in-class hybrid retrieval with minimal code.
- **Positive:** Semantic Kernel `AzureAISearchVectorStore` is first-party — low integration cost.
- **Positive:** Free tier covers the entire showcase.
- **Negative:** Two separate stores (AI Search + Cosmos DB) instead of one — slightly more infrastructure.
- **Risk:** AI Search free tier limited to 50 MB / 10,000 documents; sufficient for showcase but must be monitored.
- **Mitigation:** Add index size to the Application Insights dashboard; alert at 80 % capacity.
