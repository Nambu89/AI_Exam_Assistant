// =============================================================================
// Private Endpoints — AIServices/Foundry, AI Search, Key Vault, ACR
// =============================================================================
// Each Private Endpoint lands in the PE subnet and is bound to the matching
// Private DNS zone(s) via a privateDnsZoneGroup, so in-VNet clients resolve the
// service FQDN to its private IP. Deployed only when private networking is on.
// -----------------------------------------------------------------------------

@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}
@description('Resource id of the Private Endpoints subnet.')
param peSubnetId string

// Target service ids
@description('AIServices (Foundry) account resource id.')
param foundryAccountId string
@description('AI Search service resource id.')
param searchId string
@description('Key Vault resource id.')
param keyVaultId string
@description('Container Registry resource id.')
param acrId string

// Private DNS zone ids
@description('DNS zone ids for the AIServices account: cognitiveservices, openai, services.ai.')
param foundryDnsZoneIds array
@description('privatelink.search.windows.net zone id.')
param searchDnsZoneId string
@description('privatelink.vaultcore.azure.net zone id.')
param keyVaultDnsZoneId string
@description('privatelink.azurecr.io zone id.')
param acrDnsZoneId string

// ---------------------------------------------------------------------------
// AIServices / Foundry — groupId "account". Bound to all three AI DNS zones.
// ---------------------------------------------------------------------------
resource foundryPe 'Microsoft.Network/privateEndpoints@2025-07-01' = {
  name: 'pe-foundry'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'foundry'
        properties: {
          privateLinkServiceId: foundryAccountId
          groupIds: ['account']
        }
      }
    ]
  }
}

resource foundryDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-07-01' = {
  parent: foundryPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      for (zoneId, i) in foundryDnsZoneIds: {
        name: 'config-${i}'
        properties: {
          privateDnsZoneId: zoneId
        }
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// AI Search — groupId "searchService".
// ---------------------------------------------------------------------------
resource searchPe 'Microsoft.Network/privateEndpoints@2025-07-01' = {
  name: 'pe-search'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'search'
        properties: {
          privateLinkServiceId: searchId
          groupIds: ['searchService']
        }
      }
    ]
  }
}

resource searchDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-07-01' = {
  parent: searchPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'search'
        properties: {
          privateDnsZoneId: searchDnsZoneId
        }
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Key Vault — groupId "vault".
// ---------------------------------------------------------------------------
resource keyVaultPe 'Microsoft.Network/privateEndpoints@2025-07-01' = {
  name: 'pe-keyvault'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'keyvault'
        properties: {
          privateLinkServiceId: keyVaultId
          groupIds: ['vault']
        }
      }
    ]
  }
}

resource keyVaultDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-07-01' = {
  parent: keyVaultPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'keyvault'
        properties: {
          privateDnsZoneId: keyVaultDnsZoneId
        }
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Azure Container Registry — groupId "registry" (requires Premium SKU).
// ---------------------------------------------------------------------------
resource acrPe 'Microsoft.Network/privateEndpoints@2025-07-01' = {
  name: 'pe-acr'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'acr'
        properties: {
          privateLinkServiceId: acrId
          groupIds: ['registry']
        }
      }
    ]
  }
}

resource acrDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-07-01' = {
  parent: acrPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'acr'
        properties: {
          privateDnsZoneId: acrDnsZoneId
        }
      }
    ]
  }
}
