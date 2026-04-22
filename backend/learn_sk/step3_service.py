import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Load endpoint + deployment name from .env (no API key needed)
load_dotenv()

ENDPOINT   = "https://ershi-mn10asmm-eastus2.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-5.4-mini"

# DefaultAzureCredential checks (in order):
#   1. Azure CLI  →  az login           (local dev)
#   2. Managed Identity                  (production on Azure)
# No API key ever stored in code or .env
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

# Step 1: Create the Kernel
kernel = Kernel()

# Step 2: Add Azure OpenAI service using your Azure identity
service = AzureChatCompletion(
    deployment_name=DEPLOYMENT,
    endpoint=ENDPOINT,
    ad_token_provider=token_provider,   # identity-based auth, no key
)

kernel.add_service(service)

# Step 3: Confirm
print("Services registered:", list(kernel.services.keys()))
print("Endpoint  :", ENDPOINT)
print("Deployment:", DEPLOYMENT)
# Expected:
# Services registered: ['gpt-5.4-mini']
# Endpoint  : https://ershi-mn10asmm-eastus2.cognitiveservices.azure.com/
# Deployment: gpt-5.4-mini
