"""
LLMOps Step 1 — LLM Tracing
Configures OpenTelemetry with Azure Monitor exporter.
Enables Semantic Kernel's built-in LLM span instrumentation.

Every LLM call produces a span with:
  - model name, deployment
  - prompt tokens, completion tokens
  - latency (start → first token → last token)
  - full prompt + response (sensitive mode — disable if PII risk)
"""
import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger(__name__)


def setup_telemetry(app_insights_connection_string: str) -> None:
    """Call once at app startup to wire OTel → App Insights."""
    if not app_insights_connection_string:
        logger.warning("Telemetry: APPLICATIONINSIGHTS_CONNECTION_STRING not set — tracing disabled.")
        return

    # Enable SK's built-in LLM span instrumentation
    # Emits spans for every kernel invocation and every LLM call
    os.environ.setdefault(
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS", "true"
    )
    # Also log prompt content + response (set to "false" if users send PII)
    os.environ.setdefault(
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE", "true"
    )

    # Wire Azure Monitor as the OTel exporter
    # This sends traces, logs, and metrics to App Insights automatically
    configure_azure_monitor(
        connection_string=app_insights_connection_string,
        logger_name="investment_coach",   # captures all loggers under this namespace
    )

    logger.info("Telemetry: OTel → App Insights configured.")
