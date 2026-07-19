// =============================================================================
// Networking — VNet, subnets, Private DNS zones + VNet links
// =============================================================================
// Deployed only when deployPrivateNetworking = true. Provides:
//   - A VNet with two subnets:
//       * infra  (/23) — hosts the Container Apps (workload-profiles) environment;
//                        delegated to Microsoft.App/environments (required).
//       * pe     (/24) — holds the Private Endpoints; network policies disabled.
//   - The Private DNS zones for every privatised backing service, each linked to
//     the VNet so the VNet-injected Container Apps resolve private IPs automatically.
// -----------------------------------------------------------------------------

@description('VNet name.')
param name string
@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}

@description('VNet address space.')
param addressPrefix string = '10.0.0.0/16'
@description('Container Apps infrastructure subnet prefix (workload profiles need >= /27; /23 gives ample room).')
param infraSubnetPrefix string = '10.0.0.0/23'
@description('Private Endpoints subnet prefix.')
param peSubnetPrefix string = '10.0.2.0/24'

// Private DNS zones required by the privatised services. The three AI zones cover
// the AIServices/Foundry account (cognitiveservices + openai + services.ai names).
var privateDnsZoneNames = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.search.windows.net'
  'privatelink.vaultcore.azure.net'
  'privatelink.azurecr.io'
]

resource vnet 'Microsoft.Network/virtualNetworks@2025-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [addressPrefix]
    }
    subnets: [
      {
        // Container Apps (workload profiles) infrastructure subnet.
        name: 'snet-containerapps'
        properties: {
          addressPrefix: infraSubnetPrefix
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        // Private Endpoints subnet — policies disabled so PEs can be created.
        name: 'snet-private-endpoints'
        properties: {
          addressPrefix: peSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// --- Private DNS zones + VNet links (one per zone) ---
resource dnsZones 'Microsoft.Network/privateDnsZones@2024-06-01' = [
  for zone in privateDnsZoneNames: {
    name: zone
    location: 'global'
    tags: tags
  }
]

resource dnsLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = [
  for (zone, i) in privateDnsZoneNames: {
    parent: dnsZones[i]
    name: 'link-${name}'
    location: 'global'
    tags: tags
    properties: {
      registrationEnabled: false
      virtualNetwork: {
        id: vnet.id
      }
    }
  }
]

output vnetId string = vnet.id
output infraSubnetId string = vnet.properties.subnets[0].id
output peSubnetId string = vnet.properties.subnets[1].id

// Map of DNS zone name -> resource id (indexed by callers).
output dnsZoneIds object = toObject(
  privateDnsZoneNames,
  zone => zone,
  zone => resourceId('Microsoft.Network/privateDnsZones', zone)
)
