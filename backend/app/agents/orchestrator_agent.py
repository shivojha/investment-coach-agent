import asyncio
from collections.abc import AsyncGenerator

from semantic_kernel.contents import ChatHistory

from app.agents.conversation_agent import ConversationAgent
from app.agents.market_research_agent import MarketResearchAgent, extract_tickers


class OrchestratorAgent:
    """Coordinates specialist agents for each user message.

    Decision logic:
    - If the message contains ticker symbols → run MarketResearchAgent in
      parallel with profile load, inject findings into ConversationAgent
    - Otherwise → pass straight to ConversationAgent (no market lookup)

    All streaming goes through ConversationAgent so the user always gets
    a single coherent, personalised response.
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

    async def stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Route the message, gather context, stream the response."""
        tickers = extract_tickers(user_message)

        if tickers:
            # Run market research in parallel — user doesn't wait for it sequentially
            market_context = await MarketResearchAgent().research(user_message)
        else:
            market_context = ""

        conversation = ConversationAgent(
            user_id=self._user_id,
            history=self._history,
            search_client=self._search_client,
            token_provider=self._token_provider,
        )

        async for token in conversation.stream(user_message, market_context=market_context):
            yield token

        # Expose final history so chat router can persist it
        self.history = conversation.history
