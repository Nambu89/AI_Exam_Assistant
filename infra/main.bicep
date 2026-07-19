// =============================================================================
// AI Exam Assistant — main deployment (subscription scope)
// =============================================================================
// Provisions the full Azure footprint for the multi-agent study app:
//   - User-assigned managed identity (keyless auth everywhere possible)
//   - Azure AI Foundry (Cognitive Services kind=AIServices) account + project
//     + GPT-5 family model deployments (EU Data Zone) + Content Safety
//   - Azure AI Search (Foundry IQ agentic retrieval + GraphRAG vector store)
//   - Azure Key Vault
//   - Log Analytics + Application Insights (OpenTelemetry backend)
//   - Azure Container Registry
//   - Azure Container Apps environment + backend & frontend container apps
//   - RBAC role assignments granting the managed identity least-privilege access
//
// Deploy with:  azd up   (azd sets AZURE_ENV_NAME / AZURE_LOCATION / AZURE_PRINCIPAL_ID)
// Validate with: az bicep build --file infra/main.bicep
// -----------------------------------------------------------------------------

targetScope = 'subscription'

// ------------------------------- Parameters ---------------------------------

@minLength(1)
@maxLength(64)
@description('Name of the azd environment; used to derive resource names and the resource group.')
param environmentName string

@description('EU Data Zone region for all resources. Foundry Data Zone Standard deployments keep data within the EU. Verified GPT-5 availability regions include swedencentral, westeurope, francecentral, polandcentral.')
@allowed([
  'swedencentral'
  'westeurope'
  'francecentral'
  'polandcentral'
  'norwayeast'
])
param location string = 'swedencentral'

@description('Object id of the user/service principal running the deploy. Granted data-plane roles so a human can also use the resources. azd populates AZURE_PRINCIPAL_ID.')
param principalId string = ''

// --- GPT-5 family deployment names (never GPT-4, per project policy) ---
@description('Tutor / general reasoning model deployment name.')
param chatModel string = 'gpt-5.4-mini'
@description('Cheap routing + GraphRAG entity-extraction model deployment name.')
param routerModel string = 'gpt-5-nano'
@description('Deep reasoning model deployment name (essay correction, hard-question validation).')
param reasoningModel string = 'gpt-5.5'
@description('LLM-as-judge model deployment name for evaluations.')
param judgeModel string = 'gpt-5-mini'
@description('Embedding model deployment name.')
param embeddingModel string = 'text-embedding-3-large'

// Container images. azd overrides these after building & pushing to ACR.
// Default to a public placeholder so the very first `azd provision` succeeds.
@description('Backend container image. azd replaces this on deploy.')
param backendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
@description('Frontend container image. azd replaces this on deploy.')
param frontendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ------------------------------- Naming -------------------------------------

// A short, deterministic token keeps globally-unique names stable per environment.
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var prefix = 'aiexam'
var tags = {
  'azd-env-name': environmentName
  application: 'ai-exam-assistant'
}

// azd creates/uses one resource group per environment.
resource rg 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

// ------------------------------- Modules -------------------------------------

// --- User-assigned managed identity (consumed by the Container Apps) ---
module identity 'modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    name: 'id-${prefix}-${resourceToken}'
    location: location
    tags: tags
  }
}

// --- Observability: Log Analytics + Application Insights ---
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    logAnalyticsName: 'log-${prefix}-${resourceToken}'
    appInsightsName: 'appi-${prefix}-${resourceToken}'
    location: location
    tags: tags
  }
}

// --- Key Vault (secrets the app may still need, e.g. 3rd-party keys) ---
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: 'kv-${prefix}-${take(resourceToken, 12)}'
    location: location
    tags: tags
    // Grant the MI (and the deploying principal) Key Vault Secrets User.
    principalIds: union([identity.outputs.principalId], empty(principalId) ? [] : [principalId])
  }
}

// --- Azure AI Search (Foundry IQ agentic retrieval + GraphRAG vectors) ---
// Grantees: the app's MI, the deploying human, AND the Foundry account identity
// (Foundry IQ agentic retrieval calls Search using the Foundry resource identity).
module search 'modules/search.bicep' = {
  name: 'search'
  scope: rg
  params: {
    name: 'srch-${prefix}-${resourceToken}'
    location: location
    tags: tags
    principalIds: union(
      [identity.outputs.principalId, foundry.outputs.accountPrincipalId],
      empty(principalId) ? [] : [principalId]
    )
  }
}

// --- Azure AI Foundry: AIServices account + project + GPT-5 deployments ---
module foundry 'modules/ai-foundry.bicep' = {
  name: 'foundry'
  scope: rg
  params: {
    accountName: 'aif-${prefix}-${resourceToken}'
    projectName: 'proj-exam'
    location: location
    tags: tags
    // Deployed models (GPT-5 family + embeddings). EU Data Zone SKU.
    modelDeployments: [
      { name: chatModel, model: 'gpt-5.4-mini', sku: 'DataZoneStandard', capacity: 100 }
      { name: routerModel, model: 'gpt-5-nano', sku: 'DataZoneStandard', capacity: 100 }
      { name: reasoningModel, model: 'gpt-5.5', sku: 'DataZoneStandard', capacity: 50 }
      { name: judgeModel, model: 'gpt-5-mini', sku: 'DataZoneStandard', capacity: 50 }
      { name: embeddingModel, model: 'text-embedding-3-large', sku: 'Standard', capacity: 120 }
    ]
    // MI (and deployer) get Azure AI User for data-plane calls.
    principalIds: union([identity.outputs.principalId], empty(principalId) ? [] : [principalId])
  }
}

// --- Container Registry (holds the images azd builds) ---
module registry 'modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    name: '${prefix}acr${resourceToken}'
    location: location
    tags: tags
    // MI pulls images with AcrPull (no admin user / no credentials).
    pullPrincipalId: identity.outputs.principalId
  }
}

// --- Container Apps environment + backend & frontend apps ---
module containerApps 'modules/container-apps.bicep' = {
  name: 'container-apps'
  scope: rg
  params: {
    location: location
    tags: tags
    environmentName: 'cae-${prefix}-${resourceToken}'
    backendAppName: 'ca-${prefix}-backend'
    frontendAppName: 'ca-${prefix}-frontend'
    backendImage: backendImage
    frontendImage: frontendImage
    // Identity used to pull images and to authenticate to Foundry/Search.
    userAssignedIdentityId: identity.outputs.id
    userAssignedIdentityClientId: identity.outputs.clientId
    registryLoginServer: registry.outputs.loginServer
    logAnalyticsCustomerId: monitoring.outputs.logAnalyticsCustomerId
    logAnalyticsSharedKey: monitoring.outputs.logAnalyticsSharedKey
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    // App configuration wired to the provisioned services.
    foundryProjectEndpoint: foundry.outputs.projectEndpoint
    contentSafetyEndpoint: foundry.outputs.accountEndpoint
    searchEndpoint: search.outputs.endpoint
    chatModel: chatModel
    routerModel: routerModel
    reasoningModel: reasoningModel
    judgeModel: judgeModel
    embeddingModel: embeddingModel
  }
}

// ------------------------------- Outputs -------------------------------------
// azd captures these into the environment (.azure/<env>/.env) and CI reads them.

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_TENANT_ID string = tenant().tenantId

output AZURE_CLIENT_ID string = identity.outputs.clientId
output AZURE_MANAGED_IDENTITY_ID string = identity.outputs.id

// Foundry / models
output FOUNDRY_PROJECT_ENDPOINT string = foundry.outputs.projectEndpoint
output FOUNDRY_ACCOUNT_ENDPOINT string = foundry.outputs.accountEndpoint
output CHAT_MODEL string = chatModel
output ROUTER_MODEL string = routerModel
output REASONING_MODEL string = reasoningModel
output JUDGE_MODEL string = judgeModel
output EMBEDDING_MODEL string = embeddingModel

// Retrieval / guardrails
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_CONTENT_SAFETY_ENDPOINT string = foundry.outputs.accountEndpoint

// Platform
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.endpoint
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.appInsightsConnectionString

// Service URLs
output SERVICE_BACKEND_URI string = containerApps.outputs.backendUri
output SERVICE_FRONTEND_URI string = containerApps.outputs.frontendUri
