import asyncio
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

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

settings = AzureChatPromptExecutionSettings(max_completion_tokens=200)


async def main():
    history = ChatHistory()
    history.add_system_message(
        "You are a friendly investment coach. Keep answers concise."
    )
    history.add_user_message("In 3 bullet points, what should a beginner know about investing?")

    chat_service = kernel.get_service(type=AzureChatCompletion)

    print("Coach: ", end="", flush=True)

    full_response = ""

    # invoke_stream() returns chunks as they arrive — one or a few tokens at a time
    async for chunk in chat_service.get_streaming_chat_message_content(
        chat_history=history,
        settings=settings,
    ):
        if chunk and chunk.content:
            print(chunk.content, end="", flush=True)  # print each chunk immediately
            full_response += chunk.content

    print("\n")  # new line after streaming finishes

    # Save the full response to history (same as before)
    history.add_assistant_message(full_response)

    print(f"Total characters received: {len(full_response)}")
    print(f"Total messages in history: {len(history.messages)}")

asyncio.run(main())
