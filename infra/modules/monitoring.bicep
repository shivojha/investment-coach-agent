// Azure Monitor — Log Analytics + Application Insights
// Cost: FREE tier
//   - First 5 GB/month ingestion free for both services
//   - Showcase will not exceed this
//   ⚠️ Set daily cap to prevent accidental overrun beyond 5 GB

@description('Base name prefix for monitoring resources')
param name string

@description('Environment suffix')
param env string

@description('Azure region')
param location string

// ── Log Analytics Workspace ───────────────────────────────────────────────────
// Central log store — Container Apps and App Insights both write here

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-${name}-${env}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'   // pay-per-GB — first 5 GB/month free
    }
    retentionInDays: 30   // minimum paid retention; free tier keeps 90 days
    workspaceCapping: {
      dailyQuotaGb: 1     // ⚠️ hard cap at 1 GB/day — prevents surprise bills
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ── Application Insights ──────────────────────────────────────────────────────
// Tracks: request latency, token counts, errors, custom metrics per turn

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${name}-${env}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id   // workspace-based — required for free tier
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    RetentionInDays: 30
    DisableIpMasking: false   // mask IPs for privacy
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
