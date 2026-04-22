from collections.abc import AsyncGenerator

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

from app.config import settings
from app.plugins.user_profile import UserProfilePlugin

SYSTEM_PROMPT = """
You are a friendly, expert investment coach helping users plan their financial future.

Your behaviour:
- On first contact greet the user warmly and ask profiling questions one at a time:
  age, income range, risk tolerance, investment goals, time horizon, existing assets.
- Use ProfilePlugin.get_profile() at the start of every conversation to check
  if the user already has a saved profile. Skip questions already answered.
- After the user shares profile information, call ProfilePlugin.save_profile()
  to persist it immediately.
- Once you have enough profile data, give tailored investment suggestions
  (asset classes and allocation strategy — not specific stock picks).
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


class InvestmentCoachAgent:
    """Streaming investment coach agent.
    One instance is created per request — lightweight because the Kernel
    is cheap to create; only the Azure clients are singletons.
    """

    def __init__(self, user_id: str, history: ChatHistory, search_client, token_provider):
        self.user_id = user_id
        self.history = history

        self.kernel = _build_kernel(token_provider)
        self.kernel.add_plugin(
            UserProfilePlugin(search_client),
            plugin_name="ProfilePlugin",
        )

        self._chat_service = self.kernel.get_service(type=AzureChatCompletion)
        self._settings = AzureChatPromptExecutionSettings(
            max_completion_tokens=400,
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

    async def stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Add the user message, stream the assistant reply token by token."""
        if not self.history.messages:
            self.history.add_system_message(
                SYSTEM_PROMPT + f"\nCurrent user_id: {self.user_id}"
            )

        self.history.add_user_message(user_message)

        full_response = ""
        async for chunk in self._chat_service.get_streaming_chat_message_content(
            chat_history=self.history,
            settings=self._settings,
            kernel=self.kernel,
        ):
            if chunk and chunk.content:
                full_response += chunk.content
                yield chunk.content

        self.history.add_assistant_message(full_response)
