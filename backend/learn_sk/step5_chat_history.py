import asyncio
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatHistory

settings = AzureChatPromptExecutionSettings(max_completion_tokens=100)

ENDPOINT   = "https://ershi-mn10asmm-eastus2.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-5.4-mini"

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

kernel = Kernel()
kernel.add_service(AzureChatCompletion(
    deployment_name=DEPLOYMENT,
    endpoint=ENDPOINT,
    ad_token_provider=token_provider,
))

async def main():
    # ChatHistory holds the full conversation — system + user + assistant turns
    history = ChatHistory()

    # System message: sets the AI's persona for the whole conversation
    history.add_system_message(
        "You are a friendly investment coach. "
        "Keep answers short and beginner-friendly."
    )

    # Get the chat service from the kernel so we can call it directly
    chat_service = kernel.get_service(type=ChatCompletionClientBase)

    # --- Turn 1 ---
    history.add_user_message("What is a stock?")
    response = await chat_service.get_chat_message_content(history, settings=settings)
    history.add_assistant_message(str(response))   # save reply to history
    print(f"User : What is a stock?")
    print(f"Coach: {response}\n")

    # --- Turn 2 ---
    # Notice: we say "it" — the AI knows "it" means stock because of history
    history.add_user_message("Is it risky?")
    response = await chat_service.get_chat_message_content(history, settings=settings)
    history.add_assistant_message(str(response))
    print(f"User : Is it risky?")
    print(f"Coach: {response}\n")

    # --- Turn 3 ---
    history.add_user_message("What should a beginner invest in instead?")
    response = await chat_service.get_chat_message_content(history, settings=settings)
    history.add_assistant_message(str(response))
    print(f"User : What should a beginner invest in instead?")
    print(f"Coach: {response}\n")

    # Show the full history that was built up
    print("--- Full conversation history ---")
    for msg in history.messages:
        print(f"[{msg.role}] {msg.content[:80]}...")

asyncio.run(main())
