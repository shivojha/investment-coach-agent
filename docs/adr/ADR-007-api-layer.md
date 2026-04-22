# ADR-007: API Layer Design

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

The API layer is the entry point between clients and the agent. Key decisions:
- Protocol for sending messages and receiving streamed responses
- Authentication mechanism
- Whether to place an API gateway in front of Container Apps
- API versioning strategy

---

## Decision 1: Streaming Protocol — Server-Sent Events (SSE) over WebSocket

### Options

| Option | Pros | Cons |
|--------|------|------|
| **SSE (chosen)** | HTTP/1.1 compatible, simple client-side EventSource API, works through proxies/CDNs, stateless server | Unidirectional only (client sends via POST, receives via SSE) |
| WebSocket | Full-duplex, lower overhead for high-frequency messages | Stateful connection; complicates horizontal scaling; not needed for chat cadence |
| Polling | Simplest server | High latency, wasteful bandwidth |

**Decision:** SSE. Chat is naturally request-response; the client sends a POST, the server streams
tokens back. SSE is HTTP-native, proxy-friendly, and trivial in FastAPI via `StreamingResponse`.
WebSocket adds stateful connection management with no benefit at chat message frequency.

---

## Decision 2: Authentication — Azure Entra ID JWT (Bearer Token)

### Options

| Option | Pros | Cons |
|--------|------|------|
| **Entra ID JWT (chosen)** | Azure-native, RBAC, no key management, validates audience/issuer | Requires client to obtain token; slightly more setup |
| API Key | Simple | Key rotation burden; no user identity in token |
| Anonymous | No friction | Violates NFR-04, NFR-06 |

**Decision:** Entra ID Bearer tokens. The API validates the JWT signature against the Entra ID JWKS
endpoint on every request. The `user_id` (`oid` claim) is extracted from the validated token — no
user ID is accepted from the request body (prevents impersonation). FastAPI dependency injection
makes this clean with a single `get_current_user` dependency.

---

## Decision 3: API Gateway — None for v1 (ACA built-in ingress)

### Options

| Option | Pros | Cons |
|--------|------|------|
| **ACA ingress only (chosen)** | Zero config, free, HTTPS by default | No rate limiting, no request transformation |
| Azure API Management (APIM) | Rate limiting, caching, developer portal, analytics | ~$50+/month for Developer tier; overkill for showcase |
| Azure Front Door | Global CDN, WAF, geo-routing | Cost and complexity unwarranted for single-region showcase |

**Decision:** ACA's built-in ingress (Envoy-based) is sufficient for v1. It provides HTTPS
termination and basic load balancing. Rate limiting will be implemented at the application layer
(FastAPI middleware) rather than APIM. APIM is the right v2 addition for multi-client production use.

---

## Decision 4: API Versioning — URL path prefix `/v1/`

All routes prefixed `/v1/`. Breaking changes bump to `/v2/`. Simple and industry-standard.

---

## API Contract

### `POST /v1/chat`

**Request:**
```json
{
  "session_id": "uuid",
  "message": "string"
}
```

**Headers:**
```
Authorization: Bearer <entra-id-jwt>
Content-Type: application/json
```

**Response:** `text/event-stream`
```
data: {"delta": "Based"}
data: {"delta": " on your"}
data: {"delta": " profile..."}
data: {"event": "profile_updated", "fields": ["risk_tolerance"]}
data: [DONE]
```

### `GET /v1/health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Consequences

- **Positive:** SSE is supported by every modern browser and HTTP client library — no custom protocol needed.
- **Positive:** JWT validation is stateless — any API pod can validate any token without a shared session store.
- **Positive:** No APIM cost keeps the showcase within free/near-free tier.
- **Negative:** Without APIM, per-user rate limiting requires application-level middleware.
- **Negative:** SSE requires the client to maintain two connections per turn (POST + EventSource); acceptable for web clients.
- **Risk:** Entra ID JWKS endpoint must be reachable from ACA; ensure no network policy blocks outbound to `login.microsoftonline.com`.
