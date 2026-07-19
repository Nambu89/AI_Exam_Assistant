# Infrastructure (Bicep + azd)

`azd up` provisions everything in `main.bicep` (subscription scope) and deploys the
two Container Apps. All service-to-service auth uses a **user-assigned managed
identity** with RBAC role assignments — there are no keys in app settings.

## Network posture — `deployPrivateNetworking`

A single parameter controls whether the backing services are on the public
internet or behind Private Link:

| `deployPrivateNetworking` | AI / data services | App ingress | Who can run it |
|---|---|---|---|
| `true` (default) | **Private only** — `publicNetworkAccess: Disabled` on AIServices/Foundry, AI Search, Key Vault and ACR, each fronted by a **Private Endpoint** in the VNet | **Public** (external ingress) — the only public surface | Needs VNet + Private Endpoint quota |
| `false` | Public, but still keyless (managed identity + RBAC) | Public | Anyone; no networking quota required |

### What `true` builds (matches the architecture diagram)

- **VNet** (`10.0.0.0/16`) with two subnets:
  - `snet-containerapps` **/23**, delegated to `Microsoft.App/environments` — hosts
    the VNet-injected Container Apps (workload-profiles) environment.
  - `snet-private-endpoints` **/24**, `privateEndpointNetworkPolicies: Disabled`.
- **Private DNS zones** (VNet-linked) so in-VNet clients resolve private IPs:
  `privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com`,
  `privatelink.services.ai.azure.com`, `privatelink.search.windows.net`,
  `privatelink.vaultcore.azure.net`, `privatelink.azurecr.io`.
- **Private Endpoints** for the Foundry/AIServices account (groupId `account`,
  bound to all three AI zones), AI Search (`searchService`), Key Vault (`vault`)
  and ACR (`registry`).
- Public access **disabled** on those four services (`networkAcls.defaultAction:
  Deny` where supported).

> **Result: the AI and data services are not exposed to the public internet.**
> The Container Apps environment reaches them privately; the web app's ingress is
> the only public entry point — exactly what the diagram shows.

RBAC role assignments are **kept in both modes**: Private Link secures the network
path, RBAC still authorises the identity (defence in depth).

### Toggling it off

The default is `true`. To use the public fallback (e.g. no networking quota, or to
run/debug from a laptop):

```bash
az deployment sub create ... --parameters deployPrivateNetworking=false
# or, with azd, set it as a parameter override in infra/main.parameters.json
```

## Assumptions & gotchas

- **Subnet sizing**: CA infra subnet is **/23** as requested (workload-profiles
  environments only require /27, so this is generous head-room). PE subnet is /24.
- **ACR SKU bump**: Private Endpoints require the **Premium** ACR SKU (Basic/Standard
  do not support them). The registry module auto-upgrades to Premium whenever
  `publicNetworkAccess: Disabled`, and stays **Basic** in the public fallback.
- **Image build with private ACR**: with public access disabled, an `az acr build`
  / `azd deploy` image push from outside the VNet is blocked. `networkRuleBypassOptions:
  AzureServices` lets trusted Azure build agents through; for a fully private
  pipeline, build from a self-hosted runner / agent inside the VNet.
- **Content Safety** is served by the same `kind: AIServices` account (multi-service),
  so it is covered by the Foundry Private Endpoint — no separate resource or endpoint.

## Verified API versions (Microsoft Learn, 2026-07)

| Resource | API version |
|---|---|
| `Microsoft.CognitiveServices/accounts` (+ `/projects`, `/deployments`) | `2025-06-01` |
| `Microsoft.Search/searchServices` | `2025-05-01` |
| `Microsoft.App/managedEnvironments` + `/containerApps` | `2025-07-01` |
| `Microsoft.KeyVault/vaults` | `2024-11-01` |
| `Microsoft.ContainerRegistry/registries` | `2023-11-01-preview` |
| `Microsoft.Network/virtualNetworks`, `privateEndpoints`, `privateDnsZoneGroups` | `2025-07-01` |
| `Microsoft.Network/privateDnsZones`, `virtualNetworkLinks` | `2024-06-01` |
| `Microsoft.OperationalInsights/workspaces` | `2023-09-01` |
| `Microsoft.Insights/components` | `2020-02-02` |
| `Microsoft.ManagedIdentity/userAssignedIdentities` | `2023-01-31` |
| `Microsoft.Authorization/roleAssignments` | `2022-04-01` |
