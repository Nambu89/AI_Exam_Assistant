/**
 * Realistic offline fixtures for the AZ-900 demo corpus. Shapes match
 * docs/API.md exactly so the UI renders fully with no backend.
 */
import type { ConceptMapResponse, ExamQuestion, Subject, TopicsResponse } from "@/types/api";

export const SUBJECTS: Subject[] = [
  {
    id: "az-900",
    title: "Azure Fundamentals (AZ-900)",
    topics: [
      "Cloud Concepts",
      "Azure Architecture",
      "Compute & Networking",
      "Storage",
      "Identity, Governance & Security",
      "Cost Management & Tools",
    ],
  },
];

export const TOPICS_RESPONSE: TopicsResponse = { subjects: SUBJECTS };

/** A small pool of grounded questions; the mock generator samples from these. */
export const QUESTION_BANK: ExamQuestion[] = [
  {
    id: "qb-storage-redundancy",
    stem: "Which storage redundancy option replicates data across three Azure Availability Zones in the primary region AND to a secondary region?",
    options: { A: "LRS", B: "ZRS", C: "GRS", D: "GZRS" },
    correct: "D",
    explanation:
      "GZRS (Geo-Zone-Redundant Storage) combines zone redundancy in the primary region with geo-replication to a secondary region, giving the highest durability. LRS is single-datacenter, ZRS is zonal only, and GRS geo-replicates but is locally redundant within each region.",
    topic: "Storage",
    sources: ["az-900/04-storage.md#Redundancy"],
  },
  {
    id: "qb-blob-archive",
    stem: "A team needs the lowest storage cost for compliance data that is almost never read and can tolerate hours of retrieval latency. Which Blob access tier fits best?",
    options: { A: "Hot", B: "Cool", C: "Cold", D: "Archive" },
    correct: "D",
    explanation:
      "The Archive tier has the lowest storage cost but data is offline and must be rehydrated (which can take hours) before it can be read — ideal for long-term compliance archives.",
    topic: "Storage",
    sources: ["az-900/04-storage.md#Access tiers"],
  },
  {
    id: "qb-availability-zone",
    stem: "What best describes an Azure Availability Zone?",
    options: {
      A: "A logical container for billing",
      B: "A physically separate datacenter (or group) within a Region with independent power, cooling and networking",
      C: "A pair of Regions used for disaster recovery",
      D: "A global DNS endpoint",
    },
    correct: "B",
    explanation:
      "An Availability Zone is a physically separate location within an Azure Region, each with independent power, cooling and networking, so a failure in one zone does not affect the others.",
    topic: "Azure Architecture",
    sources: ["az-900/02-azure-architecture.md#Availability Zones"],
  },
  {
    id: "qb-resource-group",
    stem: "Which statement about Resource Groups is correct?",
    options: {
      A: "A resource can belong to multiple resource groups at once",
      B: "Resource groups can be nested inside other resource groups",
      C: "A resource group holds related resources and is tied to one region for its metadata",
      D: "Resource groups replace subscriptions for billing",
    },
    correct: "C",
    explanation:
      "A resource group is a logical container for related resources; each resource lives in exactly one group, groups cannot be nested, and the group stores its metadata in a single region.",
    topic: "Azure Architecture",
    sources: ["az-900/02-azure-architecture.md#Resource Groups"],
  },
  {
    id: "qb-capex-opex",
    stem: "Moving from on-premises servers to a pay-as-you-go cloud model is primarily a shift from…",
    options: {
      A: "OpEx to CapEx",
      B: "CapEx to OpEx",
      C: "IaaS to SaaS",
      D: "Public to private cloud",
    },
    correct: "B",
    explanation:
      "Buying hardware up front is a capital expense (CapEx). Paying for cloud resources as you consume them is an operational expense (OpEx), which improves cash flow and elasticity.",
    topic: "Cloud Concepts",
    sources: ["az-900/01-cloud-concepts.md#CapEx vs OpEx"],
  },
  {
    id: "qb-shared-responsibility",
    stem: "In the shared responsibility model, who is always responsible for the security of the physical datacenter?",
    options: {
      A: "The customer",
      B: "The cloud provider (Microsoft)",
      C: "Shared equally regardless of service model",
      D: "A third-party auditor",
    },
    correct: "B",
    explanation:
      "Physical security of datacenters is always Microsoft's responsibility. What the customer owns shifts with the service model (IaaS/PaaS/SaaS), but physical hosts, network and facilities remain with the provider.",
    topic: "Cloud Concepts",
    sources: ["az-900/01-cloud-concepts.md#Shared responsibility"],
  },
  {
    id: "qb-aks",
    stem: "Which Azure compute service is a managed Kubernetes offering for orchestrating containers?",
    options: {
      A: "Azure Container Instances (ACI)",
      B: "Azure Kubernetes Service (AKS)",
      C: "Azure App Service",
      D: "Azure Functions",
    },
    correct: "B",
    explanation:
      "AKS is Azure's managed Kubernetes service for orchestrating containers at scale. ACI runs single containers without orchestration, App Service hosts web apps, and Functions is event-driven serverless compute.",
    topic: "Compute & Networking",
    sources: ["az-900/03-compute-and-networking.md#AKS"],
  },
  {
    id: "qb-expressroute",
    stem: "A customer needs a private, dedicated connection to Azure that does not traverse the public internet. Which service should they use?",
    options: {
      A: "VPN Gateway",
      B: "ExpressRoute",
      C: "Virtual Network peering",
      D: "Azure DNS",
    },
    correct: "B",
    explanation:
      "ExpressRoute provides a private, dedicated connection to Azure through a connectivity provider, bypassing the public internet for higher reliability and lower latency. A VPN Gateway is encrypted but runs over the internet.",
    topic: "Compute & Networking",
    sources: ["az-900/03-compute-and-networking.md#ExpressRoute"],
  },
  {
    id: "qb-conditional-access",
    stem: "Which Microsoft Entra ID capability enforces policies such as 'require MFA when signing in from an untrusted location'?",
    options: {
      A: "Role-Based Access Control (RBAC)",
      B: "Conditional Access",
      C: "Azure Policy",
      D: "Resource locks",
    },
    correct: "B",
    explanation:
      "Conditional Access evaluates signals (user, location, device, risk) and applies controls like requiring MFA or blocking access. RBAC governs what an identity can do; Azure Policy governs resource configuration.",
    topic: "Identity, Governance & Security",
    sources: ["az-900/05-identity-governance-security.md#Conditional Access"],
  },
  {
    id: "qb-rbac-vs-policy",
    stem: "What is the key difference between Azure RBAC and Azure Policy?",
    options: {
      A: "They are two names for the same feature",
      B: "RBAC controls what actions identities can perform; Azure Policy enforces rules about resource properties/configuration",
      C: "Azure Policy manages user passwords; RBAC manages billing",
      D: "RBAC only applies to storage accounts",
    },
    correct: "B",
    explanation:
      "RBAC answers 'who can do what' (permissions on resources). Azure Policy answers 'what state resources are allowed to be in' (e.g., only allowed regions/SKUs, required tags). They complement each other.",
    topic: "Identity, Governance & Security",
    sources: [
      "az-900/05-identity-governance-security.md#RBAC",
      "az-900/05-identity-governance-security.md#Azure Policy",
    ],
  },
  {
    id: "qb-tco-calculator",
    stem: "Which tool estimates the cost savings of migrating from on-premises infrastructure to Azure?",
    options: {
      A: "Pricing Calculator",
      B: "Total Cost of Ownership (TCO) Calculator",
      C: "Azure Advisor",
      D: "Cost Management + Billing",
    },
    correct: "B",
    explanation:
      "The TCO Calculator compares on-premises costs with the equivalent Azure spend to estimate migration savings. The Pricing Calculator estimates the cost of a specific set of Azure services you configure.",
    topic: "Cost Management & Tools",
    sources: ["az-900/06-cost-management-and-tools.md#TCO Calculator"],
  },
  {
    id: "qb-composite-sla",
    stem: "When you chain two Azure services (each with a 99.9% SLA) in a dependent workflow, the composite SLA…",
    options: {
      A: "Increases to 99.99%",
      B: "Stays at 99.9%",
      C: "Decreases (multiply the two SLAs)",
      D: "Is not affected by dependencies",
    },
    correct: "C",
    explanation:
      "For dependent services the composite SLA is the product of the individual SLAs (0.999 × 0.999 ≈ 99.8%), so combining services can lower the effective availability.",
    topic: "Cost Management & Tools",
    sources: ["az-900/06-cost-management-and-tools.md#Composite SLAs"],
  },
];

/** GraphRAG-style concept map for AZ-900 (offline co-occurrence graph). */
export const CONCEPT_MAP: ConceptMapResponse = {
  subject: "az-900",
  backend: "graphrag",
  communities: [
    {
      id: 0,
      title: "Cloud concepts & economics",
      summary:
        "Foundational cloud ideas: the public, private and hybrid deployment models; the IaaS/PaaS/SaaS service models; the shift from capital expenditure (CapEx) to operational expenditure (OpEx); and the shared responsibility model that splits security duties between customer and provider depending on the service model.",
    },
    {
      id: 1,
      title: "Azure global infrastructure",
      summary:
        "How Azure is organised physically and logically: Regions and region pairs, Availability Zones for high availability, and the management hierarchy of Management Groups, Subscriptions and Resource Groups, all provisioned through Azure Resource Manager (ARM).",
    },
    {
      id: 2,
      title: "Compute & networking",
      summary:
        "Ways to run workloads and connect them: Virtual Machines and Scale Sets, App Service, container options (ACI and AKS), serverless Functions, plus Virtual Networks, VPN Gateway and ExpressRoute for private connectivity.",
    },
    {
      id: 3,
      title: "Storage services & redundancy",
      summary:
        "The Azure Storage account and its data services (Blob, Files, Queue, Table), Blob access tiers for cost control, and the redundancy options LRS, ZRS, GRS and GZRS that trade cost against durability and geographic protection.",
    },
    {
      id: 4,
      title: "Identity, governance & security",
      summary:
        "Microsoft Entra ID for authentication and single sign-on, MFA and Conditional Access, RBAC for authorization, Zero Trust and defense in depth as security principles, and governance tools like Azure Policy, resource locks and Microsoft Defender for Cloud.",
    },
    {
      id: 5,
      title: "Cost management & tools",
      summary:
        "Understanding and controlling spend: Cost Management, the Pricing and TCO calculators, SLAs and composite SLAs, and the tooling surface — the Azure portal, CLI, PowerShell, Cloud Shell, Azure Arc and infrastructure as code with ARM/Bicep.",
    },
  ],
  nodes: [
    { id: "Public Cloud", label: "Public Cloud", community: 0, size: 5 },
    { id: "Private Cloud", label: "Private Cloud", community: 0, size: 4 },
    { id: "Hybrid Cloud", label: "Hybrid Cloud", community: 0, size: 5 },
    { id: "IaaS", label: "IaaS", community: 0, size: 6 },
    { id: "PaaS", label: "PaaS", community: 0, size: 6 },
    { id: "SaaS", label: "SaaS", community: 0, size: 5 },
    { id: "CapEx vs OpEx", label: "CapEx vs OpEx", community: 0, size: 5 },
    { id: "Shared Responsibility", label: "Shared Responsibility", community: 0, size: 6 },

    { id: "Azure Region", label: "Azure Region", community: 1, size: 8 },
    { id: "Region Pair", label: "Region Pair", community: 1, size: 5 },
    { id: "Availability Zone", label: "Availability Zone", community: 1, size: 8 },
    { id: "Resource Group", label: "Resource Group", community: 1, size: 7 },
    { id: "Subscription", label: "Subscription", community: 1, size: 6 },
    { id: "Management Group", label: "Management Group", community: 1, size: 5 },
    { id: "Azure Resource Manager", label: "Azure Resource Manager", community: 1, size: 6 },

    { id: "Virtual Machine", label: "Virtual Machine", community: 2, size: 7 },
    { id: "VM Scale Sets", label: "VM Scale Sets", community: 2, size: 4 },
    { id: "App Service", label: "App Service", community: 2, size: 5 },
    { id: "Azure Kubernetes Service", label: "AKS", community: 2, size: 6 },
    { id: "Container Instances", label: "ACI", community: 2, size: 4 },
    { id: "Azure Functions", label: "Azure Functions", community: 2, size: 5 },
    { id: "Virtual Network", label: "Virtual Network", community: 2, size: 7 },
    { id: "VPN Gateway", label: "VPN Gateway", community: 2, size: 4 },
    { id: "ExpressRoute", label: "ExpressRoute", community: 2, size: 5 },

    { id: "Storage Account", label: "Storage Account", community: 3, size: 8 },
    { id: "Blob Storage", label: "Blob Storage", community: 3, size: 7 },
    { id: "Azure Files", label: "Azure Files", community: 3, size: 4 },
    { id: "Access Tiers", label: "Access Tiers", community: 3, size: 5 },
    { id: "LRS", label: "LRS", community: 3, size: 4 },
    { id: "ZRS", label: "ZRS", community: 3, size: 4 },
    { id: "GRS", label: "GRS", community: 3, size: 4 },
    { id: "GZRS", label: "GZRS", community: 3, size: 4 },

    { id: "Microsoft Entra ID", label: "Microsoft Entra ID", community: 4, size: 8 },
    { id: "Multi-Factor Auth", label: "MFA", community: 4, size: 5 },
    { id: "Conditional Access", label: "Conditional Access", community: 4, size: 5 },
    { id: "RBAC", label: "RBAC", community: 4, size: 6 },
    { id: "Zero Trust", label: "Zero Trust", community: 4, size: 5 },
    { id: "Azure Policy", label: "Azure Policy", community: 4, size: 6 },
    { id: "Defender for Cloud", label: "Defender for Cloud", community: 4, size: 5 },

    { id: "Cost Management", label: "Cost Management", community: 5, size: 6 },
    { id: "Pricing Calculator", label: "Pricing Calculator", community: 5, size: 5 },
    { id: "TCO Calculator", label: "TCO Calculator", community: 5, size: 5 },
    { id: "SLA", label: "SLA", community: 5, size: 5 },
    { id: "Azure Arc", label: "Azure Arc", community: 5, size: 4 },
    { id: "Bicep", label: "Bicep", community: 5, size: 4 },
    { id: "Cloud Shell", label: "Cloud Shell", community: 5, size: 4 },
  ],
  edges: [
    { source: "IaaS", target: "PaaS", weight: 3 },
    { source: "PaaS", target: "SaaS", weight: 3 },
    { source: "Shared Responsibility", target: "IaaS", weight: 4 },
    { source: "Shared Responsibility", target: "SaaS", weight: 3 },
    { source: "CapEx vs OpEx", target: "Public Cloud", weight: 2 },
    { source: "Public Cloud", target: "Hybrid Cloud", weight: 3 },
    { source: "Private Cloud", target: "Hybrid Cloud", weight: 3 },

    { source: "Azure Region", target: "Availability Zone", weight: 6 },
    { source: "Azure Region", target: "Region Pair", weight: 4 },
    { source: "Azure Region", target: "Resource Group", weight: 3 },
    { source: "Resource Group", target: "Subscription", weight: 5 },
    { source: "Subscription", target: "Management Group", weight: 4 },
    { source: "Azure Resource Manager", target: "Resource Group", weight: 4 },
    { source: "Azure Resource Manager", target: "Subscription", weight: 3 },

    { source: "Virtual Machine", target: "VM Scale Sets", weight: 4 },
    { source: "Virtual Machine", target: "Virtual Network", weight: 5 },
    { source: "Azure Kubernetes Service", target: "Container Instances", weight: 3 },
    { source: "App Service", target: "Azure Functions", weight: 2 },
    { source: "Virtual Network", target: "VPN Gateway", weight: 4 },
    { source: "Virtual Network", target: "ExpressRoute", weight: 4 },
    { source: "Virtual Machine", target: "Availability Zone", weight: 3 },

    { source: "Storage Account", target: "Blob Storage", weight: 6 },
    { source: "Storage Account", target: "Azure Files", weight: 4 },
    { source: "Blob Storage", target: "Access Tiers", weight: 5 },
    { source: "Storage Account", target: "LRS", weight: 3 },
    { source: "Storage Account", target: "ZRS", weight: 3 },
    { source: "Storage Account", target: "GRS", weight: 3 },
    { source: "Storage Account", target: "GZRS", weight: 3 },
    { source: "ZRS", target: "Availability Zone", weight: 3 },

    { source: "Microsoft Entra ID", target: "Multi-Factor Auth", weight: 5 },
    { source: "Microsoft Entra ID", target: "Conditional Access", weight: 5 },
    { source: "Microsoft Entra ID", target: "RBAC", weight: 4 },
    { source: "Conditional Access", target: "Multi-Factor Auth", weight: 4 },
    { source: "Zero Trust", target: "Conditional Access", weight: 3 },
    { source: "RBAC", target: "Subscription", weight: 3 },
    { source: "Azure Policy", target: "Defender for Cloud", weight: 3 },
    { source: "Azure Policy", target: "Subscription", weight: 3 },

    { source: "Cost Management", target: "Pricing Calculator", weight: 4 },
    { source: "Pricing Calculator", target: "TCO Calculator", weight: 4 },
    { source: "Cost Management", target: "Subscription", weight: 3 },
    { source: "SLA", target: "Availability Zone", weight: 3 },
    { source: "Azure Arc", target: "Hybrid Cloud", weight: 4 },
    { source: "Bicep", target: "Azure Resource Manager", weight: 4 },
    { source: "Cloud Shell", target: "Azure Resource Manager", weight: 2 },
  ],
};

/** Canned grounded answers keyed by intent for the mock chat. */
export interface CannedAnswer {
  keywords: string[];
  answer: string;
  sources: string[];
}

export const CHAT_ANSWERS: CannedAnswer[] = [
  {
    keywords: ["availability zone", "zone", "datacenter"],
    answer:
      "An **Availability Zone** is a physically separate location within an Azure Region — each zone has independent power, cooling and networking. Because zones fail independently, deploying across two or more zones protects a workload from a datacenter-level outage. Zones are the building block behind zone-redundant services such as ZRS storage.",
    sources: [
      "az-900/02-azure-architecture.md#Availability Zones",
      "az-900/04-storage.md#Redundancy",
    ],
  },
  {
    keywords: ["redundancy", "lrs", "zrs", "grs", "gzrs", "durability"],
    answer:
      "Azure Storage offers four redundancy options, from lowest to highest durability:\n\n- **LRS** — three copies inside one datacenter.\n- **ZRS** — copies across three Availability Zones in the primary region.\n- **GRS** — LRS in the primary region plus asynchronous copies to a secondary region.\n- **GZRS** — ZRS in the primary region plus geo-replication to a secondary region (highest durability).\n\nChoose based on how much you need to survive: a rack, a datacenter, a zone, or a whole region.",
    sources: ["az-900/04-storage.md#Redundancy"],
  },
  {
    keywords: ["blob", "tier", "hot", "cool", "archive"],
    answer:
      "**Blob access tiers** let you trade storage cost against access cost:\n\n- **Hot** — frequent access, highest storage cost.\n- **Cool** — infrequent access, ≥ 30 days.\n- **Cold** — rarely accessed, ≥ 90 days, still online.\n- **Archive** — offline, lowest storage cost, must be *rehydrated* before reading.\n\nLifecycle policies can move blobs between tiers automatically as they age.",
    sources: ["az-900/04-storage.md#Access tiers"],
  },
  {
    keywords: ["entra", "identity", "sso", "sign in", "authentication"],
    answer:
      "**Microsoft Entra ID** is Azure's cloud identity and access management service. It handles **authentication** (proving who you are), **single sign-on**, and integrates **MFA** and **Conditional Access** to strengthen sign-ins. Authorization — what an identity can *do* — is then handled by **RBAC**.",
    sources: ["az-900/05-identity-governance-security.md#Microsoft Entra ID"],
  },
  {
    keywords: ["rbac", "role", "permission", "authorization"],
    answer:
      "**Role-Based Access Control (RBAC)** grants identities permissions by assigning *roles* (like Reader, Contributor, Owner) at a scope (management group, subscription, resource group or resource). RBAC answers *'who can do what'*, while **Azure Policy** governs *'what state resources may be in'*.",
    sources: ["az-900/05-identity-governance-security.md#RBAC"],
  },
  {
    keywords: ["capex", "opex", "cost", "pricing", "tco", "billing"],
    answer:
      "The cloud shifts spending from **CapEx** (buying hardware up front) to **OpEx** (paying for what you consume). To plan spend, use the **Pricing Calculator** to estimate a configuration of services, and the **TCO Calculator** to compare on-premises costs against Azure for migrations. **Cost Management** then tracks and alerts on actual spend.",
    sources: [
      "az-900/01-cloud-concepts.md#CapEx vs OpEx",
      "az-900/06-cost-management-and-tools.md#Calculators",
    ],
  },
  {
    keywords: ["resource group", "subscription", "management group", "hierarchy"],
    answer:
      "Azure's management hierarchy nests four levels: **Management Groups** → **Subscriptions** → **Resource Groups** → **resources**. A resource group is a logical container for related resources, tied to one region for its metadata; policies and RBAC applied higher up are inherited downward.",
    sources: ["az-900/02-azure-architecture.md#Management hierarchy"],
  },
];

export const FALLBACK_ANSWER =
  "Great question. For AZ-900 it helps to anchor each topic to the knowledge graph: cloud concepts and economics, Azure's global infrastructure, compute & networking, storage & redundancy, identity/governance/security, and cost & tools. Ask me about a specific service (for example *'What is GZRS?'* or *'How does Conditional Access work?'*) and I'll ground the answer in the study corpus.";

export const FALLBACK_SOURCES = ["az-900/README.md#What this is"];
