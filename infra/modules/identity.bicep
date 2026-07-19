// User-assigned managed identity shared by the Container Apps.
// Keyless auth: this identity is granted RBAC on Foundry, Search, Key Vault, ACR.

@description('Managed identity name.')
param name string
@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

output id string = uami.id
output name string = uami.name
output principalId string = uami.properties.principalId
output clientId string = uami.properties.clientId
