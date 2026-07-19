// Azure AI Search — backs Foundry IQ agentic retrieval and the GraphRAG vector store.
// RBAC (Entra) data-plane auth is enabled; the managed identity is granted both
// data-plane (index read/write) and control-plane (create indexes/indexers) roles.

@description('Search service name (globally unique, lowercase).')
param name string
@description('Location.')
param location string
@description('Resource tags.')
param tags object = {}
@description('Principal ids granted Search data + service roles.')
param principalIds array = []

// Built-in roles
var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7' // read/write index documents
var searchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'   // manage indexes/indexers/knowledge

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    // Basic is enough for the demo corpus; scale to standard for larger indexes.
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    // Entra ID (keyless) auth for the data plane; disable API keys.
    authOptions: null
    disableLocalAuth: true
    hostingMode: 'Default'
    semanticSearch: 'standard' // required for Foundry IQ agentic retrieval + semantic ranking
    publicNetworkAccess: 'enabled'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

resource indexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for pid in principalIds: {
    name: guid(search.id, pid, searchIndexDataContributorRoleId)
    scope: search
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        searchIndexDataContributorRoleId
      )
      principalId: pid
    }
  }
]

resource serviceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for pid in principalIds: {
    name: guid(search.id, pid, searchServiceContributorRoleId)
    scope: search
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        searchServiceContributorRoleId
      )
      principalId: pid
    }
  }
]

output id string = search.id
output name string = search.name
output endpoint string = 'https://${search.name}.search.windows.net'
output principalId string = search.identity.principalId
