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
import os


def setup_telemetry() -> None:
    """Configure OTel → App Insights. Reads APPLICATIONINSIGHTS_CONNECTION_STRING from env.
    Must be called at module level before FastAPI app is created.
    """
    conn_str = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not conn_str:
        print("Telemetry: APPLICATIONINSIGHTS_CONNECTION_STRING not set — tracing disabled.")
        return

    # Enable SK's built-in LLM span instrumentation before any kernel is created
    os.environ.setdefault("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS", "true")
    os.environ.setdefault("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE", "true")

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor()   # auto-reads APPLICATIONINSIGHTS_CONNECTION_STRING from env
        print("Telemetry: OTel → App Insights configured.")
    except Exception as e:
        print(f"Telemetry: configure_azure_monitor failed — {e}")
