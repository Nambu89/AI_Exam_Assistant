# Azure Architecture and Management

## Physical infrastructure: datacenters, regions, and zones

Azure's physical foundation is a global network of **datacenters** — facilities full of servers, storage, and networking hardware. Customers do not interact with datacenters directly; they are grouped into higher-level constructs.

- An **Azure Region** is a geographical area containing one or more datacenters that are near one another and connected by a low-latency network. When you deploy a resource, you choose a region (for example, *West Europe* or *East US*). Most Azure services are deployed into a region.
- **Azure Availability Zones** are physically separate datacenters within a single Azure Region. Each zone has independent power, cooling, and networking, and zones are connected by high-speed, private fiber. Because a failure in one zone does not affect the others, placing resources across multiple Availability Zones provides **high availability** and protection against datacenter-level failures. Availability Zones are used with **zone-redundant** services such as zonal virtual machines and zone-redundant storage.
- **Region pairs**: Most regions are paired with another region in the same geography, usually at least 300 miles apart. **Region pairs** provide disaster recovery: if one region fails, its pair can take over, and planned Azure platform updates are rolled out to only one region in a pair at a time. Data residency stays within the same geography, which helps meet compliance requirements. Example: *West Europe* is paired with *North Europe*.
- **Sovereign regions**: Isolated instances of Azure for specific compliance or legal needs, such as **Azure Government** (US) and **Azure China** (operated by 21Vianet). Sovereign regions are physically and logically separate from the global Azure cloud.

## Azure resources and Azure Resource Manager

An **Azure resource** is any manageable item in Azure — a virtual machine, a storage account, a database, a virtual network, and so on. Everything you create in Azure is a resource.

**Azure Resource Manager (ARM)** is the deployment and management service for Azure. Every request to create, update, or delete a resource — whether it comes from the Azure portal, Azure CLI, Azure PowerShell, or a REST API — passes through ARM. ARM provides:

- **Consistent management** across all tools (the portal, CLI, and PowerShell all call the same ARM API).
- **Declarative templates** (ARM templates and **Bicep**) that describe the desired state of resources so deployments are repeatable.
- **Access control, tagging, and grouping** at the resource level.

## Resource Groups

A **Resource Group** is a logical container that holds related Azure resources. Key rules and relationships:

- Every resource must belong to **exactly one** Resource Group.
- A resource can be moved between Resource Groups.
- A Resource Group **is tied to one Region for its metadata** — you specify a region when you create the Resource Group, and that region stores information about the group. However, the resources inside a Resource Group can live in different regions.
- Deleting a Resource Group deletes all resources inside it, which makes Resource Groups a convenient unit for managing the lifecycle of an application.
- Access control (Azure RBAC) and policies applied to a Resource Group are inherited by the resources inside it.

## Subscriptions

An **Azure Subscription** is a logical unit of Azure services linked to an Azure account, and it is a **boundary for billing and access control**. A subscription:

- Groups together Resource Groups (and therefore resources) for billing — each subscription produces its own invoice.
- Has **service limits and quotas** (for example, a maximum number of virtual machines per region).
- Can be used to separate environments (production vs. development), organizations, or cost centers.

An account can hold multiple subscriptions. Every Resource Group belongs to exactly one Subscription.

## Management Groups

A **Management Group** is a container that sits **above subscriptions**, letting you organize multiple subscriptions into a hierarchy and apply governance to all of them at once. When you apply an **Azure Policy** or **Azure RBAC** assignment to a Management Group, it is **inherited** by all subscriptions and resources beneath it. Management Groups can be nested (a Management Group can contain other Management Groups), up to several levels deep, and all Management Groups roll up to a single **root management group** per Azure Active Directory / Microsoft Entra tenant.

## The management hierarchy

Azure organizes governance and billing in a four-level hierarchy, from broadest to narrowest scope:

**Management Group → Subscription → Resource Group → Resource**

- A **Management Group** contains one or more **Subscriptions** (and optionally other Management Groups).
- A **Subscription** contains one or more **Resource Groups**.
- A **Resource Group** contains one or more **Resources**.
- A **Resource** is the actual service instance (VM, database, etc.).

The defining relationship is **inheritance**: policies, role-based access control assignments, and organizational structure applied at a higher scope flow **downward** to everything beneath. This means you can set a rule once at the Management Group level and have it govern hundreds of subscriptions automatically. Understanding this hierarchy is central to governance in Azure, because it determines where a control takes effect and how broadly it applies.
