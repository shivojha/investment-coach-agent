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

# --- Define a Plugin ---
# A plugin is just a Python class.
# @kernel_function marks methods the AI is allowed to call.
class UserProfilePlugin:
    """Stores and retrieves user investment profiles."""

    def __init__(self):
        # Pretend this is a database — just a dict for now
        self._profiles = {}

    @kernel_function(description="Get the investment profile for a user")
    def get_profile(self, user_id: str) -> str:
        profile = self._profiles.get(user_id)
        if not profile:
            return "No profile found — user is new."
        return profile

    @kernel_function(description="Save the user's investment profile")
    def save_profile(self, user_id: str, profile: str) -> str:
        self._profiles[user_id] = profile
        return f"Profile saved for {user_id}."


async def main():
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        deployment_name=DEPLOYMENT,
        endpoint=ENDPOINT,
        ad_token_provider=token_provider,
    ))

    # Register the plugin on the Kernel — give it a name
    kernel.add_plugin(UserProfilePlugin(), plugin_name="ProfilePlugin")

    # Tell the AI it is allowed to call plugin functions automatically
    settings = AzureChatPromptExecutionSettings(
        max_completion_tokens=200,
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    history = ChatHistory()
    history.add_system_message(
        "You are an investment coach. "
        "When you need a user's profile, use the ProfilePlugin to get or save it. "
        "The current user_id is 'user-123'."
    )

    # Turn 1 — AI will call get_profile() automatically to check if user exists
    history.add_user_message("Do you know anything about my investment goals?")
    response = await kernel.invoke_prompt(
        prompt="{{$history}}",
        history=history,
        settings=settings,
    )
    print(f"Coach: {response}\n")

    # Turn 2 — AI will call save_profile() to remember this
    history.add_user_message("I'm 30 years old, moderate risk, saving for retirement in 30 years.")
    response = await kernel.invoke_prompt(
        prompt="{{$history}}",
        history=history,
        settings=settings,
    )
    print(f"Coach: {response}\n")

    # Show registered plugins
    print("--- Plugins on the Kernel ---")
    for name, plugin in kernel.plugins.items():
        print(f"  {name}: {list(plugin.functions.keys())}")

asyncio.run(main())
