from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI
    aoai_endpoint: str
    aoai_api_key: str
    aoai_chat_deployment: str = "gpt-4o"
    aoai_embedding_deployment: str = "text-embedding-3-small"

    # Azure AI Search
    ai_search_endpoint: str
    ai_search_key: str
    ai_search_index: str = "user-profiles"

    # Azure Cosmos DB
    cosmos_connection: str
    cosmos_database: str = "investment-coach"
    cosmos_container: str = "chat-history"

    # Azure Entra ID
    entra_tenant_id: str
    entra_client_id: str

    # App
    use_local_secrets: bool = False
    chat_history_max_turns: int = 20
    session_ttl_seconds: int = 86400

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
