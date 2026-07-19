// =============================================================================
// Azure Container Apps — environment + backend and frontend apps
// =============================================================================
// Both apps run under the SAME user-assigned managed identity, which is used to
// (a) pull images from ACR (AcrPull) and (b) authenticate to Foundry/Search with
// no keys. The backend's env vars are wired to the provisioned services.
//
// The `azd-service-name` tag tells azd which app maps to which service in azure.yaml.
// -----------------------------------------------------------------------------

@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}

@description('Container Apps managed environment name.')
param environmentName string
@description('Backend container app name.')
param backendAppName string
@description('Frontend container app name.')
param frontendAppName string

@description('Backend image (azd overrides on deploy).')
param backendImage string
@description('Frontend image (azd overrides on deploy).')
param frontendImage string

@description('Resource id of the user-assigned managed identity.')
param userAssignedIdentityId string
@description('Client id of the user-assigned managed identity (for DefaultAzureCredential).')
param userAssignedIdentityClientId string
@description('ACR login server (e.g. myacr.azurecr.io).')
param registryLoginServer string

@description('Log Analytics workspace customer id.')
param logAnalyticsCustomerId string
@description('Log Analytics workspace shared key.')
@secure()
param logAnalyticsSharedKey string
@description('Application Insights connection string (OpenTelemetry sink).')
param appInsightsConnectionString string

@description('Container Apps infrastructure subnet id for VNet injection. Empty = no VNet (public fallback).')
param infrastructureSubnetId string = ''

// --- App configuration wired to provisioned services ---
param foundryProjectEndpoint string
param contentSafetyEndpoint string
param searchEndpoint string
param chatModel string
param routerModel string
param reasoningModel string
param judgeModel string
param embeddingModel string

var vnetEnabled = !empty(infrastructureSubnetId)

// --- Managed environment ---
// When a subnet is supplied the environment is VNet-injected with a Consumption
// workload profile (required for injection). `internal: false` keeps the app
// ingress public — the only intended public surface — while the environment
// reaches the backing services privately over the Private Endpoints. VNet-linked
// Private DNS zones give the apps automatic private-IP resolution.
resource environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    workloadProfiles: vnetEnabled
      ? [
          {
            name: 'Consumption'
            workloadProfileType: 'Consumption'
          }
        ]
      : null
    vnetConfiguration: vnetEnabled
      ? {
          infrastructureSubnetId: infrastructureSubnetId
          internal: false
        }
      : null
  }
}

// --- Backend Container App (FastAPI + Microsoft Agent Framework) ---
resource backend 'Microsoft.App/containerApps@2025-07-01' = {
  name: backendAppName
  location: location
  // Tag lets `azd deploy` target this app for the "backend" service.
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000 // uvicorn
        transport: 'auto'
        corsPolicy: {
          allowedOrigins: ['*']
        }
      }
      registries: [
        {
          server: registryLoginServer
          identity: userAssignedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
          env: [
            { name: 'MODEL_PROVIDER', value: 'foundry' }
            { name: 'KNOWLEDGE_BACKEND', value: 'auto' }
            // DefaultAzureCredential picks THIS user-assigned identity.
            { name: 'AZURE_CLIENT_ID', value: userAssignedIdentityClientId }
            { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundryProjectEndpoint }
            { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
            { name: 'FOUNDRY_KNOWLEDGE_BASE', value: 'exam-knowledge' }
            { name: 'CHAT_MODEL', value: chatModel }
            { name: 'ROUTER_MODEL', value: routerModel }
            { name: 'REASONING_MODEL', value: reasoningModel }
            { name: 'JUDGE_MODEL', value: judgeModel }
            { name: 'EMBEDDING_MODEL', value: embeddingModel }
            { name: 'ENABLE_CONTENT_SAFETY', value: 'true' }
            { name: 'AZURE_CONTENT_SAFETY_ENDPOINT', value: contentSafetyEndpoint }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'CORS_ORIGINS', value: 'https://${frontendAppName}.${environment.properties.defaultDomain}' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

// --- Frontend Container App (static build served by e.g. nginx) ---
resource frontend 'Microsoft.App/containerApps@2025-07-01' = {
  name: frontendAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
      registries: [
        {
          server: registryLoginServer
          identity: userAssignedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            // Vite reads VITE_* at build time; provided here for runtime config shims.
            { name: 'VITE_API_URL', value: 'https://${backend.properties.configuration.ingress.fqdn}/api' }
            { name: 'VITE_USE_MOCKS', value: 'false' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output environmentId string = environment.id
output backendUri string = 'https://${backend.properties.configuration.ingress.fqdn}'
output frontendUri string = 'https://${frontend.properties.configuration.ingress.fqdn}'
