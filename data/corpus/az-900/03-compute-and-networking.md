# Azure Compute and Networking

## Compute services

Azure offers several ways to run workloads, ranging from full control (virtual machines) to fully managed serverless code.

### Azure Virtual Machines (VMs)

**Azure Virtual Machines** are on-demand, scalable computing resources that give you a virtualized server in the cloud. A VM is an **Infrastructure as a Service (IaaS)** offering: you control the operating system, installed software, and configuration, while Azure manages the physical hardware. VMs are ideal when you need total control, want to run legacy applications, or must migrate ("lift and shift") existing servers.

- **Availability Sets** protect against hardware failures *within a single datacenter* by distributing VMs across **fault domains** (groups sharing a power source and network switch) and **update domains** (groups that can be rebooted together during maintenance). This ensures not all VMs go down at the same time.
- **Virtual Machine Scale Sets (VMSS)** let you create and manage a group of identical, load-balanced VMs that automatically increase or decrease in number in response to demand. Scale Sets are Azure's primary tool for **horizontal scaling (scale out/in)** of VMs, and they support **autoscaling**, delivering elasticity.

While Availability Sets protect against failures inside one datacenter, spreading VMs or Scale Sets across **Availability Zones** protects against a whole datacenter failing.

### Azure App Service

**Azure App Service** is a **Platform as a Service (PaaS)** offering for hosting web applications, REST APIs, and mobile back ends. Azure manages the operating system, patching, and load balancing; you deploy your code and configure scaling. App Service supports multiple languages and includes built-in autoscaling, deployment slots, and custom domains.

### Azure Container Instances (ACI)

**Azure Container Instances** is the fastest and simplest way to run a **container** in Azure without managing any servers. A container packages an application with its dependencies so it runs consistently anywhere. ACI is a PaaS/serverless container service, well suited to simple, short-lived, or burst workloads.

### Azure Kubernetes Service (AKS)

**Azure Kubernetes Service** is a managed **Kubernetes** offering for orchestrating large numbers of containers. Kubernetes automates deployment, scaling, and management of containerized applications. AKS manages the Kubernetes control plane for you, so you focus on the worker nodes and your workloads. Compared with ACI, AKS is designed for complex, long-running, multi-container systems that need orchestration, self-healing, and scaling.

### Azure Functions (serverless)

**Azure Functions** is a **serverless** compute service that runs small pieces of code ("functions") in response to **triggers** (an HTTP request, a timer, a message on a queue, a new blob, etc.) without you provisioning or managing any servers. You are billed only for the time your code runs (an extreme form of the consumption-based model), and the platform scales automatically. Functions are ideal for event-driven, stateless tasks.

**Relationship summary:** As you move from **Virtual Machines → App Service → Containers (ACI/AKS) → Functions**, you give up control but gain reduced management overhead — the same IaaS-to-PaaS-to-serverless spectrum seen in the shared responsibility model.

## Networking services

### Azure Virtual Network (VNet) and subnets

An **Azure Virtual Network (VNet)** is the fundamental building block for private networking in Azure. It is a logically isolated network in the cloud, defined by one or more IP address ranges, in which you place resources such as VMs. A VNet:

- Enables Azure resources to communicate securely with each other, the internet, and on-premises networks.
- Is scoped to a **single region** but can be connected to VNets in other regions.

A **subnet** is a range of IP addresses *within* a VNet used to segment the network — for example, separating web servers from database servers so that security rules can be applied per segment.

### Connecting networks: VPN Gateway and ExpressRoute

- A **VPN Gateway** is a specific type of virtual network gateway that sends encrypted traffic between an Azure VNet and an on-premises location (site-to-site) or an individual client (point-to-site) **over the public internet**. It is a common way to build a **hybrid cloud**.
- **Azure ExpressRoute** provides a **private, dedicated connection** between on-premises infrastructure and Azure through a connectivity provider — it does **not** travel over the public internet. ExpressRoute offers higher reliability, more consistent latency, and greater bandwidth than a VPN Gateway, and is used for mission-critical hybrid workloads.

### VNet peering

**VNet peering** connects two virtual networks so that resources in them can communicate as if they were on the same network, using the Microsoft backbone (not the public internet). Peering can be within a region (regional peering) or across regions (**global VNet peering**). Traffic between peered VNets is private and low-latency.

### Azure DNS

**Azure DNS** is a hosting service for **DNS domains** (the Domain Name System, which translates human-readable names like `contoso.com` into IP addresses). Azure DNS lets you manage your DNS records using the same Azure credentials, billing, and support as your other Azure services, and it uses Azure's global network of name servers for fast, reliable name resolution. Note that Azure DNS hosts domains but does not sell domain names.

**Networking relationship summary:** A **VNet** contains **subnets** that segment resources; **VNet peering** links VNets together privately; a **VPN Gateway** or **ExpressRoute** connects a VNet to on-premises; and **Azure DNS** resolves names for the resources within them.
