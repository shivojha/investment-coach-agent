// Azure Static Web Apps — React frontend hosting
// Cost: FREE tier — $0/month
//   - Includes: custom domain, HTTPS, CI/CD from GitHub, Entra ID auth
//   - 100 GB bandwidth/month free
//   ⚠️ Standard tier (~$9/month) only needed for private endpoints or SLA guarantee

@description('Name of the Static Web App')
param name string

@description('Azure region')
param location string

@description('GitHub repo URL — used for CI/CD integration')
param repositoryUrl string = 'https://github.com/investment-coach/investment-coach-agent'

@description('GitHub branch to deploy from')
param branch string = 'main'

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  sku: {
    name: 'Free'    // FREE tier — $0/month
    tier: 'Free'
  }
  properties: {
    repositoryUrl: repositoryUrl
    branch: branch
    buildProperties: {
      appLocation: 'frontend'          // Vite + React source folder
      outputLocation: 'dist'           // Vite build output folder
      appBuildCommand: 'npm run build' // build command
    }
    stagingEnvironmentPolicy: 'Disabled'  // no PR preview envs — keeps it free
    allowConfigFileUpdates: true          // allows staticwebapp.config.json changes
    enterpriseGradeCdnStatus: 'Disabled'  // enterprise CDN adds cost — disabled
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output url string = 'https://${swa.properties.defaultHostname}'
output name string = swa.name
// deploymentToken intentionally not output — contains secrets
// GitHub Actions fetches it via: az staticwebapp secrets list --name <swa-name>
