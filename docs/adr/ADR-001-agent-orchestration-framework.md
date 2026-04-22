# ADR-001: Agent Orchestration Framework

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Architecture team

---

## Context

The investment coach requires an orchestration layer that can:
- Maintain conversational context across turns
- Call tools/plugins (profile read/write, disclaimer injection)
- Connect to Azure OpenAI natively
- Support streaming responses
- Be well-supported and maintained on Azure

Three candidates were evaluated.

---

## Options Considered

### Option A — Microsoft Semantic Kernel (SK)

Microsoft's open-source SDK for building AI agents. First-class Azure OpenAI integration, Plugin model
(functions the LLM can invoke), ChatHistory abstraction, and memory connectors. Available in Python and C#.
Actively developed by Microsoft; designed explicitly for Azure AI workloads.

**Pros:**
- Native Azure OpenAI connector (no adapter needed)
- Plugin model maps directly to the `UserProfilePlugin` concept in the design
- `ChatHistory` abstraction manages the short-term context window
- Memory connector interface supports Azure AI Search out of the box
- Streaming support via `InvokeStreamingAsync`
- Microsoft-backed — good longevity signal for an Azure showcase
- Kernel can be configured with Azure Key Vault secrets via DI

**Cons:**
- Younger ecosystem than LangChain; fewer third-party integrations
- Python SDK slightly behind C# in feature parity (closing rapidly)
- Less community content / StackOverflow answers than LangChain

---

### Option B — LangChain / LangGraph

The dominant open-source agent framework with the largest ecosystem.

**Pros:**
- Huge ecosystem, extensive documentation
- LangGraph adds stateful multi-agent graph support

**Cons:**
- Azure OpenAI integration is a third-party wrapper, not first-party
- Frequent breaking changes between minor versions (operational risk)
- Plugin model is less structured; requires more boilerplate for Azure-native use
- Azure AI Search integration exists but is community-maintained
- Not from Microsoft — weaker signal for "Azure showcase"

---

### Option C — Azure AI Agent Service (Preview)

Fully managed Azure service for hosting agents, with built-in tool execution, thread management, and
file storage. No orchestration code needed.

**Pros:**
- Zero infrastructure for agent state — Azure manages threads and tool calls
- Deepest possible Azure integration
- Auto-scaling, no SDK orchestration code

**Cons:**
- Public Preview as of April 2026 — not production-ready; breaking changes possible
- Limited customisation of the plugin/tool execution loop
- Harder to run locally (no emulator)
- Less control over prompt construction and memory retrieval strategy
- Locks the system tightly to Azure — harder to test independently

---

## Decision

**Semantic Kernel (Option A)**

---

## Rationale

Semantic Kernel provides the best balance of Azure-native integration, architectural control, and
production readiness for this showcase. The Plugin model aligns exactly with the `UserProfilePlugin`
design. The Azure OpenAI connector and AI Search memory connector are first-party, reducing glue code.
It is production-stable (v1.x) unlike Azure AI Agent Service (Preview).

LangChain was ruled out because its Azure integrations are community-maintained and its rapid churn
introduces operational risk. Azure AI Agent Service is the right long-term direction but is not
preview-safe for a showcase expected to be stable.

---

## Consequences

- **Positive:** Clean plugin architecture; straightforward to unit-test plugins in isolation.
- **Positive:** Streaming is natively supported — good for UX.
- **Negative:** Team needs to learn SK's Plugin and Kernel abstractions if unfamiliar.
- **Risk:** SK Python SDK occasionally lags behind C# in new features; pin a minor version in requirements.
- **Mitigation:** Add `semantic-kernel==1.x.y` to `requirements.txt` with a Dependabot update policy.
