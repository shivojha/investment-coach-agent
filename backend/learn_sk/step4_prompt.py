import asyncio
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

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

# A prompt is just a string you send to the AI.
# {{$topic}} is a variable — SK fills it in at runtime.
prompt = "You are an investment coach. In one sentence, explain what {{$topic}} is."

# Register the prompt as a named function on the Kernel
coach_explain = kernel.add_function(
    function_name="explain",
    plugin_name="coach",
    prompt=prompt,
)

async def main():
    # Invoke the prompt, passing in the variable value
    result = await kernel.invoke(
        coach_explain,
        topic="index funds",   # replaces {{$topic}} in the prompt
    )
    print(result)

asyncio.run(main())
