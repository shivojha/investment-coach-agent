// Azure AI Search — Long-term user profile memory
// Cost: FREE tier — $0/month
//   - 1 index (we use 1: user-profiles)
//   - 50 MB storage
//   - 3 replicas max
//   Upgrade to Basic (~$73/month) only if storage exceeds 50 MB

@description('Name of the AI Search service')
param name string

@description('Azure region')
param location string

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  sku: {
    name: 'free'  // FREE tier — $0/month
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output endpoint string = 'https://${search.name}.search.windows.net'
output id string = search.id
output name string = search.name
