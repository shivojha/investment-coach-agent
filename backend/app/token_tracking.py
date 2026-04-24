"""
LLMOps Step 2 — Token Cost Tracking
Emits a custom App Insights event after every LLM call with:
  - prompt_tokens, completion_tokens, total_tokens
  - estimated_cost_usd (gpt-5.4-mini pricing)
  - user_id, session_id, agent name

Query in App Insights:
  customEvents
  | where name == "llm_token_usage"
  | project timestamp, user_id=customDimensions.user_id,
            total_tokens=customMeasurements.total_tokens,
            cost_usd=customMeasurements.estimated_cost_usd
  | order by timestamp desc
"""
import logging

from opentelemetry import trace

logger = logging.getLogger("investment_coach")

# gpt-5.4-mini pricing (as of 2026) — update if pricing changes
_COST_PER_1K_PROMPT = 0.00015       # $0.15 per 1M input tokens
_COST_PER_1K_COMPLETION = 0.00060   # $0.60 per 1M output tokens

_tracer = trace.get_tracer("investment_coach.tokens")


def record_token_usage(
    user_id: str,
    session_id: str,
    agent: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Emit token usage as an OTel span → App Insights dependency with cost attributes."""
    total = prompt_tokens + completion_tokens
    cost = (prompt_tokens / 1000 * _COST_PER_1K_PROMPT) + \
           (completion_tokens / 1000 * _COST_PER_1K_COMPLETION)

    with _tracer.start_as_current_span("llm.token_usage") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("session_id", session_id)
        span.set_attribute("agent", agent)
        span.set_attribute("prompt_tokens", prompt_tokens)
        span.set_attribute("completion_tokens", completion_tokens)
        span.set_attribute("total_tokens", total)
        span.set_attribute("estimated_cost_usd", round(cost, 6))

    logger.info(
        "token_usage agent=%s user=%s prompt=%d completion=%d total=%d cost=$%.6f",
        agent, user_id, prompt_tokens, completion_tokens, total, cost,
    )
