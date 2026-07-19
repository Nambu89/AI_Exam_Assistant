// Azure Container Registry — stores images built by `azd deploy`.
// Admin user stays disabled; the managed identity pulls images via AcrPull.

@description('ACR name (globally unique, alphanumeric, 5-50 chars).')
param name string
@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}
@description('Principal id of the managed identity granted AcrPull.')
param pullPrincipalId string

@description('Public network access. Set to Disabled when fronting the registry with a Private Endpoint.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Enabled'

// Private Endpoints require the Premium SKU (Basic/Standard are NOT supported),
// so we auto-bump to Premium whenever public access is disabled.
var sku = publicNetworkAccess == 'Disabled' ? 'Premium' : 'Basic'

// Built-in role: AcrPull
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: publicNetworkAccess
    // Let trusted Azure services (e.g. ACR Tasks builds) reach the registry.
    networkRuleBypassOptions: 'AzureServices'
  }
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullPrincipalId, acrPullRoleId)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: pullPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output id string = registry.id
output name string = registry.name
output loginServer string = registry.properties.loginServer
