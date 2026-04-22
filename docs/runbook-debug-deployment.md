# Deployment Debug Runbook

Issues encountered during initial Azure deployment and how they were fixed.
Useful for future deployments and onboarding.

---

## Issue 1 — AI Search free tier not available in eastus2

### Symptom
```
InsufficientResourcesAvailable: The region 'eastus2' is currently out of the
resources required to provision new services.
```

### Root Cause
Azure AI Search free tier has limited regional capacity. `eastus2` was out of
free-tier slots at the time of deployment.

### Fix
Added a separate `searchLocation` parameter in `main.bicep` defaulting to
`eastus` and passed it to the search module.

```bicep
param searchLocation string = 'eastus'

module search 'modules/search.bicep' = {
  params: {
    location: searchLocation  // separate from main location
  }
}
```

### Why
Free tier availability varies by region and time. Using a separate parameter
allows the search service to be deployed to any region independently of the
rest of the infrastructure.

---

## Issue 2 — Service Principal missing role assignment permission

### Symptom
```
Authorization failed for template resource of type
'Microsoft.Authorization/roleAssignments'. The client does not have permission
to perform action 'Microsoft.Authorization/roleAssignments/write'
```

### Root Cause
The Bicep `containerapps.bicep` creates a role assignment (grants Managed
Identity access to Key Vault). This requires the deploying Service Principal
to have `User Access Administrator` or `Owner` role — it only had `Contributor`.

### Fix
Granted `User Access Administrator` to the Service Principal scoped to the
resource group:

```bash
az role assignment create \
  --assignee <sp-object-id> \
  --role "User Access Administrator" \
  --scope /subscriptions/<sub-id>/resourceGroups/rg-investment-coach-demo
```

### Why
`Contributor` can create/manage resources but cannot assign roles to other
identities. Role assignments require `User Access Administrator` or `Owner`.
Scoping it to the resource group limits blast radius.

---

## Issue 3 — Cosmos DB indexing policy missing mandatory root path

### Symptom
```
BadRequest: The special mandatory indexing path "/" is not provided in any
of the path type sets.
```

### Root Cause
The custom indexing policy only specified `/user_id/?` and `/session_id/?`
in `includedPaths`. Cosmos DB requires the root path `/*` to always be
present in either included or excluded paths.

### Fix
Changed `includedPaths` to use `/*` (index everything) and moved turn content
to `excludedPaths` to save RUs:

```bicep
indexingPolicy: {
  includedPaths: [
    { path: '/*' }          // mandatory root path
  ]
  excludedPaths: [
    { path: '/turns/*' }    // exclude large content — saves RUs
    { path: '/"_etag"/?' }
  ]
}
```

### Why
Cosmos DB always requires a catch-all path in the index definition. Excluding
turn content from indexing saves ~40% of write RUs since turns are the largest
and most frequently written field.

---

## Issue 4 — OIDC federated credential wrong audience

### Symptom
```
AADSTS700212: No matching federated identity record found for presented
assertion audience 'api://AzureADTokenExchange'
```

### Root Cause
The federated credential was created with audience `api://AzureADTokenCredential`
(typo) but GitHub Actions sends `api://AzureADTokenExchange`.

### Fix
Deleted and recreated the federated credential with the correct audience:

```bash
az ad app federated-credential create \
  --id <app-id> \
  --parameters '{
    "audiences": ["api://AzureADTokenExchange"]  ← correct value
  }'
```

### Why
`api://AzureADTokenExchange` is the fixed audience value required by GitHub
Actions OIDC. It must match exactly — Azure rejects any other value.

---

## Issue 5 — Container App crashing: missing required config fields

### Symptom
```
Field required [type=missing] entra_tenant_id
Field required [type=missing] entra_client_id
```

### Root Cause
`config.py` declared `entra_tenant_id` and `entra_client_id` as required
`str` fields. The Container App environment variables didn't include them
because auth is handled by Azure Static Web Apps, not the backend.

### Fix
Made them optional with empty string defaults:

```python
entra_tenant_id: str = ""   # auth handled by ASWA
entra_client_id: str = ""
aoai_api_key: str = ""      # using Managed Identity, not API key
ai_search_key: str = ""     # using Managed Identity, not API key
```

### Why
In production the backend trusts that ASWA has already validated the user
before the request arrives. Entra ID fields are only needed for local JWT
validation which is bypassed when `USE_LOCAL_SECRETS=true`.

---

## Issue 6 — DefaultAzureCredential failing on Container App

### Symptom
```
ManagedIdentityCredential: App Service managed identity configuration not
found in environment.
AzureCliCredential: Azure CLI not found on path.
```

### Root Cause
Two sub-problems:
1. The Managed Identity was user-assigned, not system-assigned. `DefaultAzureCredential`
   needs `AZURE_CLIENT_ID` set to know which user-assigned identity to use.
2. The Managed Identity hadn't been granted the `Cognitive Services OpenAI User`
   role on the Azure OpenAI resource (which lives in a different resource group).

### Fix

**Grant role on Azure OpenAI resource:**
```bash
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<sub>/resourceGroups/poc-storage/providers/\
Microsoft.CognitiveServices/accounts/ershi-mn10asmm-eastus2
```

**Set AZURE_CLIENT_ID env var on Container App:**
```bash
az containerapp update \
  --name ca-investment-coach-demo \
  --set-env-vars "AZURE_CLIENT_ID=<managed-identity-client-id>"
```

### Why
`DefaultAzureCredential` supports multiple auth methods in order. When running
in Container Apps with a user-assigned identity, `AZURE_CLIENT_ID` must be
set explicitly — without it the SDK doesn't know which identity to use and
falls through all methods until failing. The role must also be on the specific
Azure OpenAI resource, not just the resource group.

---

## Issue 7 — ASWA free tier cannot proxy to external backends

### Symptom
Frontend sends requests to `/v1/chat` via ASWA routing rewrite — ASWA returns
empty response. UI shows no output.

### Root Cause
Azure Static Web Apps free tier routing can only rewrite to internal paths
within the same ASWA app. It cannot proxy HTTP requests to external URLs
(e.g. the Container App). The `staticwebapp.config.json` rewrite to an
external URL is silently ignored.

The Standard tier (~$9/month) supports linked backends, but free tier does not.

### Fix
Changed the React app to call the Container App URL directly using a
`VITE_API_URL` environment variable baked in at build time:

```js
// App.jsx
const API_BASE = import.meta.env.VITE_API_URL || ''
fetch(`${API_BASE}/v1/chat`, ...)
```

Set the variable in ASWA app settings (passed to Vite at build time):
```bash
az staticwebapp appsettings set \
  --name swa-investment-coach-demo \
  --setting-names VITE_API_URL=https://ca-investment-coach-demo...azurecontainerapps.io
```

Enabled CORS on the backend to allow the ASWA origin:
```python
allow_origins=["https://*.azurestaticapps.net"]
```

### Why
Vite replaces `import.meta.env.VITE_*` variables at build time. ASWA app
settings are injected as environment variables during the GitHub Actions build
step, so Vite picks them up automatically. CORS is required because the
browser is now making a cross-origin request (ASWA domain → Container App domain).

---

## Debugging Checklist for Future Issues

```
1. Backend health         curl https://<aca-fqdn>/v1/health
2. Backend logs           az containerapp logs show --name <app> --resource-group <rg> --tail 50
3. Frontend→backend       curl https://<swa-url>/v1/chat (check proxy)
4. Browser DevTools       Network tab → check status code + CORS errors
5. Deployment status      gh run list --limit 5
6. Role assignments       az role assignment list --assignee <principal-id> --all
7. Container App env vars az containerapp show --name <app> --rg <rg> --query "properties.template.containers[0].env"
```
