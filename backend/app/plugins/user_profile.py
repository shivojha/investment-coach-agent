from semantic_kernel.functions import kernel_function

# In-memory fallback when AI Search is not configured
_local_profiles: dict[str, str] = {}


class UserProfilePlugin:
    """Reads and writes user investment profiles.
    Uses Azure AI Search in production; falls back to in-memory dict locally.
    """

    def __init__(self, search_client):
        self._client = search_client  # None when AI Search not configured

    @kernel_function(description="Get the saved investment profile for the user")
    async def get_profile(self, user_id: str) -> str:
        if self._client is None:
            return _local_profiles.get(user_id, "No profile yet.")
        try:
            result = await self._client.get_document(key=user_id)
            return result.get("profile_json", "No profile yet.")
        except Exception:
            return "No profile yet."

    @kernel_function(description="Save or update the user's investment profile")
    async def save_profile(self, user_id: str, profile: str) -> str:
        if self._client is None:
            _local_profiles[user_id] = profile
            return "Profile saved."
        try:
            from app.embeddings import embed_text
            profile_text = profile
            vector = await embed_text(profile_text)
            doc = {
                "id": user_id,
                "profile_json": profile,
                "profile_text": profile_text,
                "profile_vector": vector,
            }
            await self._client.upload_documents(documents=[doc])
            return "Profile saved."
        except Exception as e:
            return f"Could not save profile: {e}"
