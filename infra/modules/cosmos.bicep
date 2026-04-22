// Azure Cosmos DB — Short-term chat history
// Cost: Serverless — ~$0 idle, < $0.01/month for showcase traffic
//   - $0.25 per million RUs consumed
//   - $0.25/GB storage
//   ⚠️ Never add throughput/autoscaleSettings — that switches to provisioned (~$24/month min)

@description('Name of the Cosmos DB account')
param name string

@description('Azure region')
param location string

var databaseName = 'investment-coach'
var containerName = 'chat-history'

// ── Cosmos DB Account ─────────────────────────────────────────────────────────

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: name
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'   // forces serverless billing — no minimum charge
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'  // best balance of consistency + cost
    }
    enableAutomaticFailover: false        // not needed for single-region demo
    publicNetworkAccess: 'Enabled'
    enableAnalyticalStorage: false        // analytical storage adds cost — disabled
  }
}

// ── Database ──────────────────────────────────────────────────────────────────

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    // No throughput or autoscaleSettings here — omitting enforces serverless
  }
}

// ── Container: chat-history ───────────────────────────────────────────────────

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: ['/user_id']   // partition by user — fast point reads per user
        kind: 'Hash'
      }
      defaultTtl: 86400       // 24 hours — sessions auto-expire, no cleanup job needed
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          { path: '/user_id/?' }
          { path: '/session_id/?' }
        ]
        excludedPaths: [
          { path: '/turns/*' }  // don't index turn content — saves RUs + cost
        ]
      }
    }
    // No throughput here either — serverless account rejects it
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output accountName string = cosmos.name
output endpoint string = cosmos.properties.documentEndpoint
// connectionString intentionally not output — contains secrets
// main.bicep calls listConnectionStrings() directly when passing to keyvault module
