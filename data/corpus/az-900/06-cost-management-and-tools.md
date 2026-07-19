# Cost Management, SLAs, and Tools

## Azure Cost Management + Billing

**Microsoft Cost Management + Billing** is a suite of tools for monitoring, allocating, and optimizing Azure spending. It lets you:

- **Analyze** costs by service, resource group, subscription, tag, or time period.
- **Set budgets** and receive **alerts** when spending approaches or exceeds a threshold.
- **Get recommendations** (via Azure Advisor) to reduce cost, such as resizing or shutting down underused resources.
- **Allocate** costs across departments or projects, often using **resource tags**.

Cost Management works hand in hand with the consumption-based (pay-as-you-go) model: because you pay for what you use, visibility into usage is essential to control spend.

## Factors that affect cost

Many factors influence how much an Azure workload costs:

- **Resource type** — different services (and their configurations) are priced differently.
- **Consumption** — how much you use; pay-as-you-go vs. **reserved capacity** (committing to one or three years for a discount).
- **Region** — prices vary by region because of local costs and regulations.
- **Bandwidth / data transfer** — inbound data is generally free, but outbound (egress) data transfer is often billed, and transfer between regions can incur charges.
- **Billing zone** for bandwidth, and any **licensing** options (for example, Azure Hybrid Benefit, which reuses existing on-premises licenses to reduce cost).

## Pricing calculator vs TCO calculator

Two free web tools help estimate cost *before* you commit:

- The **Pricing Calculator** estimates the cost of specific Azure services you plan to deploy. You add services (VMs, storage, databases), configure their size and region, and it produces a projected monthly bill. Use it to **design and price a solution**.
- The **Total Cost of Ownership (TCO) Calculator** compares the cost of running workloads **on-premises** versus **in Azure**, including hidden on-premises costs such as hardware, electricity, cooling, and IT labor. Use it to **build a business case for migrating** to the cloud.

In short: the Pricing Calculator answers "what will this Azure solution cost?", while the TCO Calculator answers "how much would I save by moving to Azure?".

## Service Level Agreements (SLAs)

A **Service Level Agreement (SLA)** is a formal commitment from Microsoft about the expected **performance and availability** (uptime) of a service, expressed as a percentage — for example, 99.9% ("three nines"). SLAs also define **service credits**: refunds a customer can claim if Microsoft fails to meet the promised level.

- Higher SLA percentages mean less allowed downtime. 99.9% permits about 8.7 hours of downtime per year; 99.99% permits about 52 minutes per year.
- **Free and preview services usually have no financial SLA.**
- You can often improve the effective availability of your own application by deploying across **Availability Zones** or multiple **regions**.

### Composite SLAs

When an application is built from **multiple services chained together**, the overall availability is a **composite SLA**, calculated by **multiplying** the individual SLAs. For example, a web app (99.95%) that depends on a database (99.99%) has a composite SLA of 0.9995 × 0.9999 ≈ **99.94%** — *lower* than either component. Adding more dependencies in series reduces overall availability. You can *raise* a composite SLA by adding **redundant, independent paths** (for example, a fallback queue), because parallel components are combined differently and increase resilience. Understanding composite SLAs is key to designing for a target availability.

## Service lifecycle: preview vs GA

Azure services and features move through a lifecycle:

- **Private preview / public preview** — early-access releases for evaluation and feedback. Preview features may change, may be incomplete, and are typically **not covered by an SLA** and not recommended for production.
- **General Availability (GA)** — the feature is fully released, supported, backed by its SLA, and recommended for production use.

Knowing whether a feature is in preview or GA is important when planning production workloads, because only GA features carry availability guarantees.

## Management and deployment tools

Azure can be managed through several interfaces, all of which ultimately call **Azure Resource Manager (ARM)**:

- **Azure portal** — a web-based, graphical interface for creating and managing resources interactively. Best for exploration, one-off tasks, and visualization via dashboards.
- **Azure PowerShell** — a set of PowerShell cmdlets (the `Az` module) for managing Azure from the command line and in scripts. Preferred by Windows-oriented administrators for automation.
- **Azure CLI** — a cross-platform command-line tool (`az` commands) for managing Azure, functionally similar to Azure PowerShell but using a different syntax. Popular in Linux and DevOps workflows.
- **Azure Cloud Shell** — a browser-based shell, available in the portal, that provides a ready-to-use environment with both Azure CLI and Azure PowerShell pre-installed and already authenticated. It requires no local setup and offers a choice of **Bash** or **PowerShell**.

### Azure Arc

**Azure Arc** extends Azure management and governance to resources **outside** Azure — on-premises servers, Kubernetes clusters, and resources in other clouds (multicloud). Once connected ("Arc-enabled"), these external resources can be managed through Azure Resource Manager and governed with the same tools (Azure Policy, RBAC, tags) as native Azure resources. Azure Arc is a key enabler of **hybrid and multicloud** management from a single control plane.

### ARM templates and Bicep

- **ARM templates** are **JSON** files that declaratively define the resources to deploy. Because they describe the *desired end state*, deployments are repeatable and idempotent — a practice known as **Infrastructure as Code (IaC)**.
- **Bicep** is a more concise, readable domain-specific language that compiles ("transpiles") down to ARM JSON. Bicep offers simpler syntax, modularity, and better authoring while producing the same ARM deployment.

**Relationship summary:** The **portal, PowerShell, CLI, and Cloud Shell** are ways to *interact* with Azure; **ARM templates and Bicep** *declare* what to deploy; **Azure Arc** *extends* that management to non-Azure resources; and **Cost Management, the Pricing/TCO calculators, and SLAs** help you *plan, control, and set expectations* for cost and reliability.
