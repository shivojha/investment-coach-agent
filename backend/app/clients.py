from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.identity import get_bearer_token_provider, DefaultAzureCredential as SyncCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField as VectorField,
)

from app.config import settings

_PLACEHOLDER = "placeholder"


def _is_configured(value: str) -> bool:
    return bool(value) and _PLACEHOLDER not in value and "<" not in value


def _build_index(name: str) -> SearchIndex:
    """Define the user-profiles index schema."""
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="profile_text", type=SearchFieldDataType.String),
            SimpleField(name="profile_json", type=SearchFieldDataType.String, filterable=False),
            VectorField(
                name="profile_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,   # text-embedding-3-small output size
                vector_search_profile_name="hnsw-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")],
        ),
    )


class AppClients:
    """Singleton container for all Azure service clients.
    AI Search and Cosmos DB are optional for local dev —
    falls back to in-memory stubs when not configured.
    """

    def __init__(self):
        self._credential = DefaultAzureCredential()
        _sync_credential = SyncCredential()

        # Always required — Azure OpenAI token provider
        self.token_provider = get_bearer_token_provider(
            _sync_credential,
            "https://cognitiveservices.azure.com/.default",
        )

        # Azure AI Search — optional for local dev
        if _is_configured(settings.ai_search_endpoint):
            self.search_client = SearchClient(
                endpoint=settings.ai_search_endpoint,
                index_name=settings.ai_search_index,
                credential=self._credential,
            )
            self.search_index_client = SearchIndexClient(
                endpoint=settings.ai_search_endpoint,
                credential=self._credential,
            )
            print("AI Search: connected.")
        else:
            self.search_client = None
            self.search_index_client = None
            print("AI Search: not configured — using in-memory profile store.")

        # Azure Cosmos DB — optional for local dev
        if _is_configured(settings.cosmos_connection):
            self.cosmos_client = CosmosClient.from_connection_string(
                settings.cosmos_connection
            )
            self._use_cosmos = True
            print("Cosmos DB: connected.")
        else:
            self.cosmos_client = None
            self._use_cosmos = False
            print("Cosmos DB: not configured — using in-memory chat history.")

    async def ensure_search_index(self) -> None:
        """Create the user-profiles index if it doesn't already exist.
        Non-fatal — app starts even if index creation fails.
        """
        if not self.search_index_client:
            return
        index_name = settings.ai_search_index
        try:
            await self.search_index_client.get_index(index_name)
            print(f"AI Search: index '{index_name}' already exists.")
        except Exception:
            try:
                await self.search_index_client.create_index(_build_index(index_name))
                print(f"AI Search: index '{index_name}' created.")
            except Exception as e:
                print(f"AI Search: could not create index '{index_name}': {e}. Falling back to in-memory.")

    async def get_cosmos_container(self):
        if not self._use_cosmos:
            return None
        db = self.cosmos_client.get_database_client(settings.cosmos_database)
        return db.get_container_client(settings.cosmos_container)

    async def close(self):
        await self._credential.close()
        if self.search_client:
            await self.search_client.close()
        if self.search_index_client:
            await self.search_index_client.close()
        if self.cosmos_client:
            await self.cosmos_client.close()


# Module-level singleton — set during app lifespan startup
clients: AppClients | None = None
