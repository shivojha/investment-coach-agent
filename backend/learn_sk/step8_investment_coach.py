import asyncio
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function

ENDPOINT   = "https://ershi-mn10asmm-eastus2.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-5.4-mini"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

# ── Plugin ────────────────────────────────────────────────────────────────────
# In production this reads/writes Azure AI Search.
# Here we use a dict to keep the example self-contained.

class UserProfilePlugin:
    """Reads and writes user investment profiles."""

    def __init__(self):
        self._store = {}

    @kernel_function(description="Get the saved investment profile for the user")
    def get_profile(self, user_id: str) -> str:
        return self._store.get(user_id, "No profile yet.")

    @kernel_function(description="Save or update the user's investment profile")
    def save_profile(self, user_id: str, profile: str) -> str:
        self._store[user_id] = profile
        return "Profile saved."


# ── Kernel setup ──────────────────────────────────────────────────────────────

def build_kernel() -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        deployment_name=DEPLOYMENT,
        endpoint=ENDPOINT,
        ad_token_provider=token_provider,
    ))
    kernel.add_plugin(UserProfilePlugin(), plugin_name="ProfilePlugin")
    return kernel


# ── Agent ─────────────────────────────────────────────────────────────────────

class InvestmentCoachAgent:
    """
    Combines: Kernel + Plugin + ChatHistory + Streaming
    This mirrors what app/routers/chat.py will do.
    """

    SYSTEM_PROMPT = """
    You are a friendly investment coach helping users plan their financial future.
    - Start by warmly greeting new users and asking profiling questions
      (age, income range, risk tolerance, goals, time horizon, existing assets).
    - Use ProfilePlugin to check if the user already has a profile.
    - Save any new profile information the user shares using ProfilePlugin.
    - Give investment suggestions tailored to the user's profile.
    - Keep answers concise and beginner-friendly.
    - Always end investment suggestions with:
      "⚠️ This is not regulated financial advice. Consult a qualified adviser."
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.kernel = build_kernel()
        self.history = ChatHistory()
        self.history.add_system_message(
            self.SYSTEM_PROMPT + f"\nCurrent user_id: {user_id}"
        )
        self.settings = AzureChatPromptExecutionSettings(
            max_completion_tokens=300,
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
        self.chat_service = self.kernel.get_service(type=AzureChatCompletion)

    async def chat(self, user_message: str) -> str:
        self.history.add_user_message(user_message)

        print(f"\nUser : {user_message}")
        print(f"Coach: ", end="", flush=True)

        full_response = ""
        async for chunk in self.chat_service.get_streaming_chat_message_content(
            chat_history=self.history,
            settings=self.settings,
            kernel=self.kernel,   # needed so the AI can call plugins
        ):
            if chunk and chunk.content:
                print(chunk.content, end="", flush=True)
                full_response += chunk.content

        print()  # newline after stream ends
        self.history.add_assistant_message(full_response)
        return full_response


# ── Run a sample conversation ─────────────────────────────────────────────────

async def main():
    print("=== Investment Coach (mini) ===\n")

    agent = InvestmentCoachAgent(user_id="user-123")

    # Simulated conversation — same flow as the real chat UI will produce
    await agent.chat("Hi, I'm new here.")
    await agent.chat("I'm 32, earn around £60k, and want to retire at 60.")
    await agent.chat("I'm not sure about risk — maybe medium?")
    await agent.chat("What should I invest in?")

    print("\n=== Conversation summary ===")
    for msg in agent.history.messages:
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        if role == "system":
            continue
        preview = msg.content[:60].replace("\n", " ") if msg.content else ""
        print(f"[{role:9}] {preview}...")

asyncio.run(main())
