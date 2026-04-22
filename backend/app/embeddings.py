from openai import AsyncAzureOpenAI

from app.config import settings

_client = AsyncAzureOpenAI(
    azure_endpoint=settings.aoai_endpoint,
    api_key=settings.aoai_api_key,
    api_version="2024-02-01",
)


async def embed_text(text: str) -> list[float]:
    response = await _client.embeddings.create(
        input=text,
        model=settings.aoai_embedding_deployment,
    )
    return response.data[0].embedding
