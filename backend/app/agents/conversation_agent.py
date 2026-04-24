from collections.abc import AsyncGenerator

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

from app.config import settings
from app.plugins.user_profile import UserProfilePlugin
from app.token_tracking import record_token_usage

SYSTEM_PROMPT = """
You are a friendly, expert investment coach helping users plan their financial future.

Your behaviour:
- The user's saved profile is injected below — treat it as ground truth.
  Skip any questions already answered in the profile.
- On first contact (empty profile) greet warmly and ask profiling questions one at a time:
  age, income range, risk tolerance, investment goals, time horizon, existing assets.
- After the user shares new profile information, call ProfilePlugin.save_profile()
  immediately to persist it.
- Once you have enough profile data, give tailored investment suggestions
  (asset classes and allocation strategy — not specific stock picks).
- If market research findings are provided in the context, use them to ground
  your answer with real data. Cite the price, sentiment, and analyst data naturally.
- Keep answers concise and beginner-friendly.
- Always end investment suggestions with this disclaimer on its own line:
  ⚠️ This is general guidance only, not regulated financial advice.
  Please consult a qualified financial adviser before investing.
"""


def _build_kernel(token_provider) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        deployment_name=settings.aoai_chat_deployment,
        endpoint=settings.aoai_endpoint,
        ad_token_provider=token_provider,
    ))
    return kernel


class ConversationAgent:
    """Streams a personalised response to the user.
    Profile is pre-loaded by the Orchestrator and injected into the system prompt.
    Market context is injected when the user mentions a ticker symbol.
    """

    def __init__(self, user_id: str, history: ChatHistory, search_client, token_provider):
        self.user_id = user_id
        self.history = history
        self._search_client = search_client

        self.kernel = _build_kernel(token_provider)
        self.kernel.add_plugin(
            UserProfilePlugin(search_client),
            plugin_name="ProfilePlugin",
        )

        self._chat_service = self.kernel.get_service(type=AzureChatCompletion)
        self._settings = AzureChatPromptExecutionSettings(
            max_completion_tokens=600,
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

    async def stream(
        self,
        user_message: str,
        profile: str = "",
        market_context: str = "",
    ) -> AsyncGenerator[str, None]:
        """Stream a response.
        profile    — pre-loaded by Orchestrator, injected into system prompt
        market_context — injected when a ticker was detected
        """
        if not self.history.messages:
            profile_section = (
                f"\n\n[User Profile]\n{profile}"
                if profile and profile != "No profile yet."
                else "\n\n[User Profile]\nNo profile yet — ask profiling questions one at a time."
            )
            self.history.add_system_message(
                SYSTEM_PROMPT + profile_section + f"\n\nuser_id: {self.user_id}"
            )

        # Inject market research as a note before the user message
        if market_context:
            augmented = (
                f"[Market Research]\n{market_context}\n\n"
                f"[User Question]\n{user_message}"
            )
        else:
            augmented = user_message

        self.history.add_user_message(augmented)

        full_response = ""
        last_metadata = {}
        async for chunk in self._chat_service.get_streaming_chat_message_content(
            chat_history=self.history,
            settings=self._settings,
            kernel=self.kernel,
        ):
            if chunk and chunk.content:
                full_response += chunk.content
                yield chunk.content
            if chunk and chunk.metadata:
                last_metadata = chunk.metadata  # last chunk carries usage stats

        self.history.add_assistant_message(full_response)

        # Emit token usage after stream completes
        usage = last_metadata.get("usage")
        if usage:
            record_token_usage(
                user_id=self.user_id,
                session_id=last_metadata.get("id", "unknown"),
                agent="conversation",
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            )
