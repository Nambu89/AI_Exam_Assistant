// =============================================================================
// Azure AI Foundry — Cognitive Services account (kind=AIServices) + project
// =============================================================================
// A single multi-service AIServices resource provides the Foundry project host,
// Azure OpenAI-compatible model endpoint, AND Content Safety (so no separate
// Content Safety resource is needed — the account endpoint serves both).
//
// Model deployments cover the GPT-5 family (never GPT-4) plus embeddings, using
// EU "Data Zone Standard" SKUs to keep inference data within the EU.
// -----------------------------------------------------------------------------

@description('AIServices (Foundry) account name.')
param accountName string
@description('Foundry project name (child of the account).')
param projectName string
@description('Location (EU Data Zone region).')
param location string
@description('Resource tags.')
param tags object = {}

@description('Model deployments: name = deployment name (used by the app), model = catalog model id, sku = deployment type, capacity = 1000s TPM.')
param modelDeployments array

@description('Principal ids granted the Azure AI User data-plane role on the account.')
param principalIds array = []

// Built-in role: Azure AI User (a.k.a. "Foundry User" after the 2026 rename).
// Use the GUID, not the name, because the display name changed during the rename.
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

// --- AIServices account (the Foundry resource) ---
resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // Required for a stable, token-issuing endpoint and for Entra data-plane auth.
    customSubDomainName: accountName
    // Enables creation of Foundry projects under this account.
    allowProjectManagement: true
    // Keyless: force Entra ID auth on the data plane, disable account keys.
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

// --- Foundry project (child resource) ---
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: account
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'AI Exam Assistant'
    description: 'Multi-agent study assistant: tutor, exam generator, grader, concept map.'
  }
}

// --- Model deployments (serialized: Cognitive Services rejects parallel creates) ---
@batchSize(1)
resource deployments 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = [
  for d in modelDeployments: {
    parent: account
    name: d.name
    sku: {
      name: d.sku
      capacity: d.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: d.model
        // version intentionally omitted -> Azure pins the current default version,
        // avoiding stale hardcoded versions. Set d.version to pin explicitly.
      }
      versionUpgradeOption: 'OnceCurrentVersionExpired'
      raiPolicyName: 'Microsoft.DefaultV2' // default Content Safety RAI policy
    }
  }
]

// --- RBAC: Azure AI User on the account (data-plane calls: chat, embeddings) ---
resource aiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for pid in principalIds: {
    name: guid(account.id, pid, azureAiUserRoleId)
    scope: account
    properties: {
      roleDefinitionId: subscriptionResourceId(
        'Microsoft.Authorization/roleDefinitions',
        azureAiUserRoleId
      )
      principalId: pid
    }
  }
]

output accountId string = account.id
output accountName string = account.name
output accountEndpoint string = account.properties.endpoint
// Foundry project endpoint format consumed by FOUNDRY_PROJECT_ENDPOINT.
output projectEndpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output accountPrincipalId string = account.identity.principalId
output projectPrincipalId string = project.identity.principalId
