// Azure Service Bus — async session-ended events
// Cost: Basic tier — ~$0.05 per million messages (~$0 at demo scale)

@description('Name of the Service Bus namespace')
param name string

@description('Azure region')
param location string

// ── Namespace ─────────────────────────────────────────────────────────────────

resource namespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'Basic'    // Basic — simple queues, ~$0 at demo scale
    tier: 'Basic'
  }
}

// ── Queue: session-ended ──────────────────────────────────────────────────────
// Published by FastAPI after each chat session; consumed by Memory Worker job

resource queue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: namespace
  name: 'session-ended'
  properties: {
    maxDeliveryCount: 3           // retry up to 3 times before dead-lettering
    lockDuration: 'PT1M'         // 1 minute to process before message reappears
    defaultMessageTimeToLive: 'P1D'  // expire after 1 day if not consumed
    deadLetteringOnMessageExpiration: true
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output connectionStringSecretName string = 'servicebus-connection'
output namespaceName string = namespace.name
output queueName string = queue.name
