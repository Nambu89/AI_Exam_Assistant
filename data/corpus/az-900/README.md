# AZ-900 Study Corpus

## What this is

This directory contains an **original study corpus** for the Microsoft **AZ-900: Microsoft Azure Fundamentals** certification. It is the demo dataset for the open-source **AI Exam Assistant**, which indexes these notes with **GraphRAG** to build a knowledge graph of Azure services, concepts, and the relationships between them.

The content is deliberately **rich in named entities** (services, features, tools) and **explicit relationships** ("an Availability Zone is a physically separate datacenter within a Region", "a Resource Group is tied to one Region for its metadata") so that the resulting knowledge graph is meaningful and queryable.

## Files

| File | Topic area |
|------|-----------|
| `01-cloud-concepts.md` | Cloud computing, benefits, CapEx/OpEx, shared responsibility, cloud & service models |
| `02-azure-architecture.md` | Regions, region pairs, Availability Zones, ARM, Resource Groups, Subscriptions, Management Groups, the management hierarchy |
| `03-compute-and-networking.md` | VMs, Scale Sets, App Service, ACI, AKS, Functions, VNets, VPN Gateway, ExpressRoute, DNS, peering |
| `04-storage.md` | Storage accounts, Blob tiers, Files, Queue, Table, disks, redundancy (LRS/ZRS/GRS/GZRS), migration tools |
| `05-identity-governance-security.md` | Microsoft Entra ID, AuthN/AuthZ, SSO, MFA, Conditional Access, RBAC, Zero Trust, defense in depth, Defender for Cloud, Azure Policy, locks, Service Trust Portal, Purview |
| `06-cost-management-and-tools.md` | Cost Management, cost factors, Pricing vs TCO calculator, SLAs & composite SLAs, preview vs GA, portal/PowerShell/CLI/Cloud Shell, Azure Arc, ARM/Bicep |

The matching gold evaluation question set lives at `../../eval/gold_qa.jsonl`.

## License and disclaimer

- This corpus is **100% original content**, written from scratch in the author's own words. It contains **no text copied from Microsoft Learn or any other source**, and is distributed under the **same license as this repository**.
- It is a **community study aid** and is **not official Microsoft material**. It is not affiliated with, endorsed by, or sponsored by Microsoft.
- "Azure", "Microsoft Entra ID", and related product names are trademarks of Microsoft and are used here only for factual, educational reference.
- Azure evolves quickly. Always confirm current service names, features, and pricing against official Microsoft documentation before relying on them for the exam or in production.
