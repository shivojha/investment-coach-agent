import asyncio
from collections.abc import AsyncGenerator

from semantic_kernel.contents import ChatHistory

from app.agents.conversation_agent import ConversationAgent
from app.agents.market_research_agent import MarketResearchAgent, extract_tickers
from app.plugins.user_profile import UserProfilePlugin


class OrchestratorAgent:
    """Coordinates specialist agents for each user message.

    On every request:
    1. Load user profile + run market research in parallel (if ticker detected)
    2. Pass both into ConversationAgent so the system prompt is grounded from the start

    Profile is loaded eagerly here — not left to the LLM to decide when to call get_profile().
    This ensures profile is always injected into the system prompt on new sessions.
    """

    def __init__(
        self,
        user_id: str,
        history: ChatHistory,
        search_client,
        token_provider,
    ):
        self._user_id = user_id
        self._history = history
        self._search_client = search_client
        self._token_provider = token_provider
        self._profile_plugin = UserProfilePlugin(search_client)

    async def stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Load profile + market data in parallel, then stream the response."""
        tickers = extract_tickers(user_message)

        # Run profile load and market research in parallel
        tasks = [self._profile_plugin.get_profile(self._user_id)]
        if tickers:
            tasks.append(MarketResearchAgent().research(user_message))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        profile = results[0] if not isinstance(results[0], Exception) else ""
        market_context = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else ""

        conversation = ConversationAgent(
            user_id=self._user_id,
            history=self._history,
            search_client=self._search_client,
            token_provider=self._token_provider,
        )

        async for token in conversation.stream(
            user_message,
            profile=profile,
            market_context=market_context,
        ):
            yield token

        # Expose final history so chat router can persist it
        self.history = conversation.history
