from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from app.config import settings

_token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

_client = AsyncAzureOpenAI(
    azure_endpoint=settings.aoai_endpoint,
    azure_ad_token_provider=_token_provider,
    api_version="2024-02-01",
)


async def embed_text(text: str) -> list[float]:
    response = await _client.embeddings.create(
        input=text,
        model=settings.aoai_embedding_deployment,
    )
    return response.data[0].embedding
