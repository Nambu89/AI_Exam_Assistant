// Azure Key Vault (RBAC authorization mode — no access policies).
// The managed identity (and optionally the deployer) get "Key Vault Secrets User".

@description('Key Vault name (globally unique, 3-24 chars).')
param name string
@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}
@description('Principal ids granted Key Vault Secrets User (data plane read of secrets).')
param principalIds array = []

// Built-in role: Key Vault Secrets User
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    // RBAC data-plane authorization (recommended over legacy access policies).
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for pid in principalIds: {
    name: guid(keyVault.id, pid, keyVaultSecretsUserRoleId)
    scope: keyVault
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        keyVaultSecretsUserRoleId
      )
      principalId: pid
      // principalType omitted so the same template works for MI and user object ids.
    }
  }
]

output id string = keyVault.id
output name string = keyVault.name
output endpoint string = keyVault.properties.vaultUri
