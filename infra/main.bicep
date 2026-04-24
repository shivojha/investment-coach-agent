// Investment Coach Agent — Azure Infrastructure
// Environment: demo
// Region: eastus2
// Est. cost: ~$0-1/month (serverless + free tiers only)
// Azure OpenAI: reusing existing instance — not provisioned here
// Container Registry: GitHub Container Registry (ghcr.io) — FREE, replaces ACR

targetScope = 'resourceGroup'

// ── Parameters ────────────────────────────────────────────────────────────────

@description('Environment name — used as suffix on all resource names')
param env string = 'demo'

@description('Azure region for all resources')
param location string = 'eastus2'

@description('Region for AI Search — free tier not available in eastus2')
param searchLocation string = 'eastus'

@description('Existing Azure OpenAI endpoint — reused from demo instance')
param aoaiEndpoint string = 'https://ershi-mn10asmm-eastus2.cognitiveservices.azure.com/'

@description('Existing Azure OpenAI chat deployment name')
param aoaiChatDeployment string = 'gpt-5.4-mini'

@description('Existing Azure OpenAI embedding deployment name')
param aoaiEmbeddingDeployment string = 'text-embedding-3-small'

@description('GitHub Container Registry image — ghcr.io/{owner}/{repo}:{tag}')
param containerImage string = 'ghcr.io/investment-coach/api:latest'

@description('GitHub username or org for ghcr.io authentication')
param ghcrUsername string

@description('GitHub PAT with read:packages scope for ghcr.io')
@secure()
param ghcrToken string

@description('Email address to receive cost alert notifications')
param alertEmail string

@description('Monthly budget threshold in USD — alert triggers at 50/80/100%')
param monthlyBudgetUsd int = 15

@description('Alpha Vantage API key for live market data')
@secure()
param alphaVantageApiKey string

// ── Naming convention ─────────────────────────────────────────────────────────

var prefix = 'investment-coach'

// ── Modules ───────────────────────────────────────────────────────────────────

module servicebus 'modules/servicebus.bicep' = {
  name: 'servicebus'
  params: {
    name: 'sb-${prefix}-${env}'
    location: location
  }
}

module search 'modules/search.bicep' = {
  name: 'search'
  params: {
    name: 'srch-${prefix}-${env}'
    location: searchLocation   // eastus — free tier not available in eastus2
  }
}

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    name: 'cosmos-${prefix}-${env}'
    location: location
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: 'kv-${prefix}-${env}'
    location: location
    aoaiEndpoint: aoaiEndpoint
    aoaiChatDeployment: aoaiChatDeployment
    aoaiEmbeddingDeployment: aoaiEmbeddingDeployment
    searchEndpoint: search.outputs.endpoint
    cosmosConnection: listConnectionStrings(
      resourceId('Microsoft.DocumentDB/databaseAccounts', 'cosmos-${prefix}-${env}'),
      '2024-05-15'
    ).connectionStrings[0].connectionString
    serviceBusNamespaceName: servicebus.outputs.namespaceName  // implicit dependsOn — listKeys runs after namespace exists
    alphaVantageApiKey: alphaVantageApiKey
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    name: prefix
    env: env
    location: location
  }
}

module containerapps 'modules/containerapps.bicep' = {
  name: 'containerapps'
  params: {
    name: 'ca-${prefix}-${env}'
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    keyVaultName: keyvault.outputs.name
    containerImage: containerImage
    ghcrUsername: ghcrUsername
    ghcrToken: ghcrToken
  }
}

module budget 'modules/budget.bicep' = {
  name: 'budget'
  params: {
    monthlyBudgetUsd: monthlyBudgetUsd
    alertEmail: alertEmail
  }
}

module staticwebapp 'modules/staticwebapp.bicep' = {
  name: 'staticwebapp'
  params: {
    name: 'swa-${prefix}-${env}'
    location: location
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output searchEndpoint string = search.outputs.endpoint
output cosmosAccountName string = cosmos.outputs.accountName
output keyVaultName string = keyvault.outputs.name
output containerAppFqdn string = containerapps.outputs.fqdn
output staticWebAppUrl string = staticwebapp.outputs.url
output serviceBusNamespace string = servicebus.outputs.namespaceName
output serviceBusQueue string = servicebus.outputs.queueName
