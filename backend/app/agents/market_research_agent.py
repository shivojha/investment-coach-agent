import asyncio
import re

from app.tools.market_data import MarketDataTool


# Matches common ticker patterns: NVDA, AAPL, BRK.B, S&P500
_TICKER_RE = re.compile(r'\b([A-Z]{1,5}(?:\.[AB])?)\b')

# Common words to exclude from ticker detection
_STOPWORDS = {
    "I", "A", "AN", "THE", "IS", "IN", "ON", "AT", "TO", "DO", "GO",
    "MY", "ME", "US", "IT", "OR", "IF", "BE", "BY", "AS", "UP", "NO",
    "SO", "AI", "UK", "US", "EU", "ETF", "IPO", "CEO", "CFO", "PE",
    "AM", "PM", "TV", "PC", "OK", "BUY", "NOW", "NEW",
}


def extract_tickers(text: str) -> list[str]:
    """Extract likely ticker symbols from user message."""
    candidates = _TICKER_RE.findall(text)
    return [t for t in candidates if t not in _STOPWORDS]


class MarketResearchAgent:
    """Fetches live market data for any tickers mentioned in the user message.
    Runs in parallel with profile load — results passed to ConversationAgent.
    """

    def __init__(self):
        self._tool = MarketDataTool()

    async def research(self, user_message: str) -> str:
        """Returns a market context string, or empty string if no tickers found."""
        tickers = extract_tickers(user_message)
        if not tickers:
            return ""

        # Cap at 2 tickers to stay within Alpha Vantage free tier limits
        tickers = tickers[:2]

        # Fetch quote + news + analyst in parallel for each ticker
        tasks = []
        for ticker in tickers:
            tasks.append(self._research_ticker(ticker))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                findings.append(result)

        return "\n\n".join(findings)

    async def _research_ticker(self, ticker: str) -> str:
        """Fetch quote, news sentiment, and analyst rating for one ticker."""
        quote, news, analyst = await asyncio.gather(
            self._tool.get_quote(ticker),
            self._tool.get_news_sentiment(ticker),
            self._tool.get_analyst_rating(ticker),
            return_exceptions=True,
        )

        parts = []
        if not isinstance(quote, Exception):
            parts.append(quote)
        if not isinstance(analyst, Exception):
            parts.append(analyst)
        if not isinstance(news, Exception):
            parts.append(f"Recent news:\n{news}")

        return "\n".join(parts)
