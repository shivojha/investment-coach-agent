from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import AzureChatCompletion


# Create the Kernel — just an empty container for now
kernel = Kernel()

print(type(kernel))           # what class it is
print(kernel.services)        # no AI services connected yet → empty dict
print(kernel.plugins)         # no plugins registered yet → empty
