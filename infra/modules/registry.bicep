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

// Built-in role: AcrPull
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
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
