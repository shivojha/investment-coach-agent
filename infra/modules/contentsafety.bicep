// Azure Content Safety — LLMOps Step 3
// Cost: Free tier — 5,000 calls/month at $0
//   Standard: $1–2 per 1,000 calls after free tier
//   Demo scale comfortably within free allowance

@description('Name of the Content Safety resource')
param name string

@description('Azure region')
param location string

resource contentSafety 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: name
  location: location
  kind: 'ContentSafety'
  sku: {
    name: 'F0'   // Free tier — 5,000 calls/month
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: name
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output endpoint string = contentSafety.properties.endpoint
output name string = contentSafety.name
