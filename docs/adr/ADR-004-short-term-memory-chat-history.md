# ADR-004: Short-Term Memory / Chat History

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

Each conversation session requires a short-term store of recent turns so the LLM has coherent
dialogue context. Requirements:
- Persist across API pod restarts (stateless API layer → external store needed)
- Fast read/write per turn (< 20 ms target)
- TTL-based expiry for stale sessions (24 h)
- Query by `user_id` + `session_id`
- Low cost / operational overhead

---

## Options Considered

### Option A — Azure Cosmos DB (NoSQL API, Serverless)

Document database with native TTL support, partition-key access, and serverless billing.

**Pros:**
- Native document TTL — sessions expire automatically, no cleanup job needed
- Partition by `user_id` → sub-millisecond point reads for recent turns
- Serverless tier: pay per Request Unit (RU), ~$0 at rest — ideal for showcase
- Global distribution available for production scale-out
- Managed service — no ops burden
- Stores JSON natively — chat turn arrays fit naturally
- Integrates with Azure Monitor for latency and RU consumption metrics

**Cons:**
- RU consumption must be understood to avoid unexpectedly hot partitions
- Not the fastest pure-cache option (vs Redis)
- Cosmos DB Emulator available for local dev but Docker image is large (~2 GB)

---

### Option B — Azure Cache for Redis

In-memory key-value store with optional persistence.

**Pros:**
- Fastest possible read/write (sub-millisecond)
- Native TTL per key
- Simple data model: `key = user_id:session_id`, `value = JSON array`

**Cons:**
- Basic tier (C0) costs ~$16/month — more expensive than Cosmos DB Serverless for low usage
- In-memory: data lost on restart unless Redis persistence (AOF/RDB) is enabled, adding cost
- No free tier for Azure Cache for Redis
- Storing growing chat arrays in a single Redis value requires read-modify-write; not atomic
- Weaker query capabilities — no secondary indexes, no cross-partition queries
- Adds a second non-document store to the architecture for minimal gain over Cosmos DB

---

### Option C — In-Process Memory (Python dict)

Store chat history in the API process memory only.

**Pros:**
- Zero latency, zero cost, zero infrastructure

**Cons:**
- Lost on pod restart or scale-out to multiple pods
- Violates NFR-09 (stateless API, horizontal scaling without session affinity)
- Acceptable only for single-replica local development

---

### Option D — Azure Table Storage

Lightweight Azure key-value store.

**Pros:**
- Very cheap (< $0.01/GB/month)
- Simple partition + row key model

**Cons:**
- No native TTL — requires a cleanup function (Azure Functions + Timer trigger)
- No native JSON document type — must serialise/deserialise turn arrays manually
- Inferior developer experience vs Cosmos DB for this use case
- Not idiomatic for conversational state

---

## Decision

**Azure Cosmos DB NoSQL API, Serverless tier (Option A)**

---

## Rationale

Cosmos DB Serverless provides the right blend of persistence, TTL, and zero-cost-at-rest for a
showcase workload. Its document model fits conversational turn arrays naturally, and partition-key
access by `user_id` keeps reads fast. Redis is faster in absolute terms but costs more at low
usage, has no free tier, and adds architectural complexity for minimal benefit at this scale.
In-process memory fails the stateless-API requirement. Table Storage requires a custom TTL mechanism.

---

## Consequences

- **Positive:** Sessions expire automatically — no operational cleanup job.
- **Positive:** Serverless pricing means $0 cost when idle during development.
- **Positive:** Same Azure account, same monitoring stack — no new service to learn.
- **Negative:** Cosmos DB Emulator is a large Docker image; local dev setup takes longer initially.
- **Risk:** Serverless Cosmos DB has 5,000 RU/s burst limit; unlikely to matter for showcase but worth noting.
- **Mitigation:** If higher throughput is needed, switch to provisioned autoscale (min 400 RU/s) with no code changes.
