// Azure Container Apps — API hosting
// Cost: Consumption plan — ~$0 idle (scale-to-zero)
//   - Charged per vCPU-second + memory-second only when processing requests
//   - 180,000 vCPU-seconds/month free + 360,000 GB-seconds/month free
//   - Showcase will comfortably stay within free allowance

@description('Name of the Container App')
param name string

@description('Azure region')
param location string

@description('Log Analytics workspace resource ID')
param logAnalyticsWorkspaceId string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('Key Vault name — Container App pulls secrets from here')
param keyVaultName string

@description('Full image reference — ghcr.io/{owner}/{repo}:{tag}')
param containerImage string

@description('GitHub username for ghcr.io')
param ghcrUsername string

@description('GitHub PAT with read:packages scope')
@secure()
param ghcrToken string

// ── Container Apps Environment ────────────────────────────────────────────────
// Shared environment — all container apps in this project run here

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${name}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2023-09-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2023-09-01').primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'   // scale-to-zero, ~$0 idle
      }
    ]
  }
}

// ── Managed Identity ──────────────────────────────────────────────────────────
// Used to pull secrets from Key Vault — no credentials in env vars

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${name}'
  location: location
}

// Grant the identity Key Vault Secrets User role
resource kvSecretUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, identity.id, 'Key Vault Secrets User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'  // Key Vault Secrets User built-in role
    )
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Container App ─────────────────────────────────────────────────────────────

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      // ghcr.io registry credentials
      registries: [
        {
          server: 'ghcr.io'
          username: ghcrUsername
          passwordSecretRef: 'ghcr-token'
        }
      ]
      secrets: [
        {
          name: 'ghcr-token'
          value: ghcrToken
        }
        // Key Vault secret references — pulled at startup via Managed Identity
        // Using environment().suffixes.keyvaultDns for cloud portability
        {
          name: 'aoai-endpoint'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/aoai-endpoint'
          identity: identity.id
        }
        {
          name: 'aoai-chat-deployment'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/aoai-chat-deployment'
          identity: identity.id
        }
        {
          name: 'aoai-embedding-deployment'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/aoai-embedding-deployment'
          identity: identity.id
        }
        {
          name: 'ai-search-endpoint'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/ai-search-endpoint'
          identity: identity.id
        }
        {
          name: 'cosmos-connection'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/cosmos-connection'
          identity: identity.id
        }
        {
          name: 'servicebus-connection'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/servicebus-connection'
          identity: identity.id
        }
        {
          name: 'alpha-vantage-api-key'
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/alpha-vantage-api-key'
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')    // 0.5 vCPU — sufficient for LLM I/O bound workload
            memory: '1Gi'
          }
          env: [
            { name: 'AOAI_ENDPOINT',              secretRef: 'aoai-endpoint' }
            { name: 'AOAI_CHAT_DEPLOYMENT',       secretRef: 'aoai-chat-deployment' }
            { name: 'AOAI_EMBEDDING_DEPLOYMENT',  secretRef: 'aoai-embedding-deployment' }
            { name: 'AI_SEARCH_ENDPOINT',         secretRef: 'ai-search-endpoint' }
            { name: 'COSMOS_CONNECTION',          secretRef: 'cosmos-connection' }
            { name: 'SERVICEBUS_CONNECTION',      secretRef: 'servicebus-connection' }
            { name: 'ALPHA_VANTAGE_API_KEY',      secretRef: 'alpha-vantage-api-key' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'USE_LOCAL_SECRETS',          value: 'true' }  // skip JWT — ASWA handles auth
            { name: 'AZURE_CLIENT_ID',            value: identity.properties.clientId }
          ]
        }
      ]
      scale: {
        minReplicas: 0    // scale-to-zero when idle — $0 cost at rest
        maxReplicas: 3    // scale out up to 3 replicas under load
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'  // add replica every 10 concurrent requests
              }
            }
          }
        ]
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output identityClientId string = identity.properties.clientId
