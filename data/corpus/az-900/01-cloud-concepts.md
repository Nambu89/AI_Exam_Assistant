# Cloud Concepts

## What cloud computing is

**Cloud computing** is the delivery of computing services — such as servers, storage, databases, networking, software, and analytics — over the internet ("the cloud"). Instead of owning physical hardware, an organization rents capacity from a **cloud provider** such as **Microsoft Azure**, and pays only for what it uses. The cloud provider owns and operates the physical **datacenters** where these services run.

Cloud computing separates the *consumer* of a service from the *physical infrastructure* that delivers it. This separation is what enables the core benefits below.

## Core benefits of cloud computing

- **High availability**: The ability of a service to remain operational and accessible for a high percentage of time. Cloud providers spread workloads across redundant hardware so that a single failure does not take the service down. High availability is often expressed as a target percentage of uptime (for example, 99.9%).
- **Scalability**: The ability to add or remove resources to match demand. There are two forms:
  - **Vertical scaling** (scaling up/down): increasing or decreasing the resources of a single instance — for example, adding more CPU or memory to one virtual machine.
  - **Horizontal scaling** (scaling out/in): adding or removing instances — for example, running more copies of a web server behind a load balancer.
- **Elasticity**: The ability to automatically scale resources up or down in response to real-time demand, so you have enough capacity at peak and pay less during quiet periods. Elasticity is scalability made automatic and demand-driven.
- **Reliability**: The ability of a system to recover from failures and continue functioning. Reliability is closely tied to high availability but focuses on fault tolerance and disaster recovery — often achieved by distributing resources across regions.
- **Predictability**: Confidence in both **performance** (cost-optimized, autoscaled capacity) and **cost** (transparent, forecastable spending). Predictability lets organizations plan capacity and budgets with less guesswork.
- **Security**: Cloud providers offer a broad set of controls, policies, and technologies to protect data and workloads. Customers can adopt these controls rather than building them from scratch.
- **Governance**: The ability to enforce corporate standards and regulatory requirements across all cloud resources — for example, through templates and policies that keep deployments compliant.
- **Manageability**: Two aspects — *management of the cloud* (automatically scaling, deploying from templates, monitoring health) and *management in the cloud* (using web portals, command-line tools, and APIs to administer resources).

## CapEx vs OpEx

- **Capital Expenditure (CapEx)** is an upfront, one-time spend on physical infrastructure (servers, datacenters) that is then depreciated over time. It requires large investment before any value is delivered.
- **Operational Expenditure (OpEx)** is ongoing spend on services consumed as needed, expensed in the period they are incurred. Cloud computing shifts IT spending from **CapEx to OpEx**: instead of buying servers, you rent capacity and pay a recurring bill.

## The consumption-based model

Cloud pricing typically follows a **consumption-based model** (also called pay-as-you-go): you pay only for the resources you actually use, with no upfront cost and no charge for idle capacity you release. This model reduces waste, makes costs predictable, and allows precise capacity planning. It is a direct expression of OpEx thinking.

## The shared responsibility model

The **shared responsibility model** defines which security and operational tasks belong to the **cloud provider** and which belong to the **customer**. The split depends on the service type:

- The **cloud provider** is always responsible for the **physical datacenter, physical network, and physical hosts**.
- The **customer** is always responsible for the **data, devices, and accounts/identities** they own, and for how they manage access to information.
- Responsibilities for the **operating system, network controls, applications, and identity/directory infrastructure** shift between the two parties depending on whether the service is IaaS, PaaS, or SaaS.

As you move from IaaS toward SaaS, more responsibility shifts *to the provider*.

## Cloud deployment models

- **Public cloud**: Services are owned and operated by a third-party provider (such as Azure) and delivered over the public internet. Resources are shared across many customers ("multi-tenant"). No CapEx, high scalability, but less direct control.
- **Private cloud**: Cloud computing resources used exclusively by a single organization, hosted on-premises or by a provider. Offers greater control and can meet strict regulatory needs, but the organization bears more cost and management.
- **Hybrid cloud**: Combines public and private clouds, allowing data and applications to move between them. Provides flexibility — for example, keeping sensitive data private while bursting to the public cloud for extra capacity. **Azure Arc** and **Azure VPN Gateway** are commonly used to connect the two.
- **Multicloud**: Using services from more than one public cloud provider at the same time (for example, Azure and another provider). Organizations adopt multicloud to avoid vendor lock-in or to use best-of-breed services.

## Cloud service types: IaaS, PaaS, SaaS

Cloud services are grouped into three categories, distinguished by how much the customer manages versus the provider.

- **Infrastructure as a Service (IaaS)**: The provider supplies virtualized computing infrastructure — virtual machines, storage, and networking. The customer manages the operating system, runtime, and applications. IaaS gives the most control and the most responsibility. **Example: Azure Virtual Machines.**
- **Platform as a Service (PaaS)**: The provider supplies a managed platform (operating system, middleware, runtime) on which the customer deploys applications. The customer manages only their application and data; the provider handles patching and infrastructure. **Example: Azure App Service, Azure SQL Database.**
- **Software as a Service (SaaS)**: The provider delivers fully managed, ready-to-use software over the internet. The customer manages only their data and user accounts. **Example: Microsoft 365, Dynamics 365.**

A useful relationship to remember: **IaaS → PaaS → SaaS** is a spectrum where customer responsibility decreases and provider responsibility increases at each step. The shared responsibility model and the three service types are therefore two views of the same underlying idea.
