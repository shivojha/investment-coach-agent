// Azure Key Vault — Secrets management
// Cost: FREE — Standard tier
//   - First 10,000 secret operations/month free
//   - Showcase will comfortably stay within free tier

@description('Name of the Key Vault')
param name string

@description('Azure region')
param location string

// Secrets passed in from main.bicep outputs
@description('Azure OpenAI endpoint')
param aoaiEndpoint string

@description('Azure OpenAI chat deployment name')
param aoaiChatDeployment string

@description('Azure OpenAI embedding deployment name')
param aoaiEmbeddingDeployment string

@description('Azure AI Search endpoint')
param searchEndpoint string

@description('Cosmos DB connection string')
@secure()   // marks as sensitive — never logged or shown in portal
param cosmosConnection string

@description('Service Bus namespace name — connection string fetched internally via listKeys')
param serviceBusNamespaceName string

@description('Alpha Vantage API key for market data')
@secure()
param alphaVantageApiKey string

@description('Azure Content Safety endpoint')
param contentSafetyEndpoint string

@description('Azure Content Safety resource name — key fetched via listKeys')
param contentSafetyName string

// ── Key Vault ─────────────────────────────────────────────────────────────────

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'   // standard = $0 for first 10k ops/month
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true    // use Azure RBAC — no legacy access policies
    enableSoftDelete: true           // 90-day recovery window — protects against accidents
    softDeleteRetentionInDays: 7     // minimum retention — keeps cost minimal
    enabledForTemplateDeployment: true  // allows Bicep to read secrets during deploy
    publicNetworkAccess: 'Enabled'
  }
}

// ── Secrets ───────────────────────────────────────────────────────────────────
// Container Apps will pull these at startup via Key Vault references
// No secret ever lives in code, env files, or CI/CD variables

resource secretAoaiEndpoint 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'aoai-endpoint'
  properties: {
    value: aoaiEndpoint
  }
}

resource secretAoaiChatDeployment 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'aoai-chat-deployment'
  properties: {
    value: aoaiChatDeployment
  }
}

resource secretAoaiEmbeddingDeployment 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'aoai-embedding-deployment'
  properties: {
    value: aoaiEmbeddingDeployment
  }
}

resource secretSearchEndpoint 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'ai-search-endpoint'
  properties: {
    value: searchEndpoint
  }
}

resource secretCosmosConnection 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'cosmos-connection'
  properties: {
    value: cosmosConnection
  }
}

resource secretServiceBusConnection 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'servicebus-connection'
  properties: {
    value: listKeys(
      resourceId('Microsoft.ServiceBus/namespaces/authorizationRules', serviceBusNamespaceName, 'RootManageSharedAccessKey'),
      '2022-10-01-preview'
    ).primaryConnectionString
  }
}

resource secretAlphaVantageApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'alpha-vantage-api-key'
  properties: {
    value: alphaVantageApiKey
  }
}

resource secretContentSafetyEndpoint 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'content-safety-endpoint'
  properties: {
    value: contentSafetyEndpoint
  }
}

resource secretContentSafetyKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'content-safety-key'
  properties: {
    value: listKeys(
      resourceId('Microsoft.CognitiveServices/accounts', contentSafetyName),
      '2024-04-01-preview'
    ).key1
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output name string = kv.name
output uri string = kv.properties.vaultUri
