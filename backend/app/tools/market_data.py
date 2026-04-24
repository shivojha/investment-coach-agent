import httpx
from semantic_kernel.functions import kernel_function

from app.config import settings


class MarketDataTool:
    """Semantic Kernel tool — fetches live market data from Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self._key = settings.alpha_vantage_api_key

    @kernel_function(description="Get the current stock price and basic info for a ticker symbol")
    async def get_quote(self, ticker: str) -> str:
        """Returns current price, change %, and volume for a ticker."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker.upper(),
            "apikey": self._key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.BASE_URL, params=params)
            data = resp.json().get("Global Quote", {})

        if not data:
            return f"No price data found for {ticker}."

        return (
            f"{ticker.upper()} — "
            f"Price: ${data.get('05. price', 'N/A')} | "
            f"Change: {data.get('10. change percent', 'N/A')} | "
            f"Volume: {data.get('06. volume', 'N/A')}"
        )

    @kernel_function(description="Get the latest news sentiment for a ticker symbol")
    async def get_news_sentiment(self, ticker: str) -> str:
        """Returns top 3 news headlines with sentiment scores for a ticker."""
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker.upper(),
            "limit": 3,
            "apikey": self._key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.BASE_URL, params=params)
            feed = resp.json().get("feed", [])

        if not feed:
            return f"No recent news found for {ticker}."

        lines = []
        for item in feed[:3]:
            sentiment = item.get("overall_sentiment_label", "Neutral")
            title = item.get("title", "")
            lines.append(f"[{sentiment}] {title}")

        return "\n".join(lines)

    @kernel_function(description="Get analyst recommendation for a ticker: Strong Buy, Buy, Hold, Sell")
    async def get_analyst_rating(self, ticker: str) -> str:
        """Returns analyst consensus rating and target price for a ticker."""
        params = {
            "function": "OVERVIEW",
            "symbol": ticker.upper(),
            "apikey": self._key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.BASE_URL, params=params)
            data = resp.json()

        if not data or "Symbol" not in data:
            return f"No analyst data found for {ticker}."

        return (
            f"{ticker.upper()} analyst data — "
            f"52-week high: ${data.get('52WeekHigh', 'N/A')} | "
            f"52-week low: ${data.get('52WeekLow', 'N/A')} | "
            f"P/E ratio: {data.get('PERatio', 'N/A')} | "
            f"Analyst target: ${data.get('AnalystTargetPrice', 'N/A')}"
        )
