# Identity, Governance, and Security

## Microsoft Entra ID

**Microsoft Entra ID** (formerly **Azure Active Directory**, or **Azure AD**) is Microsoft's cloud-based **identity and access management** service. It stores identities — users, groups, and applications — and controls how they sign in and what they can access. Entra ID is the identity backbone for Azure, Microsoft 365, and thousands of third-party SaaS applications. It can be synchronized with an on-premises **Active Directory** so that users have one identity across both worlds (a hybrid identity).

## Authentication vs authorization

Two distinct concepts underpin identity:

- **Authentication (AuthN)** is the process of **proving who you are** — verifying an identity through credentials such as a password, a code, or biometrics.
- **Authorization (AuthZ)** is the process of determining **what you are allowed to do** once authenticated — the permissions and access levels granted to the identity.

Authentication always comes first; authorization builds on top of it. Entra ID performs authentication, and Azure RBAC (below) performs authorization for Azure resources.

## Single sign-on (SSO) and multifactor authentication (MFA)

- **Single sign-on (SSO)** lets a user authenticate **once** and then access many applications without signing in again. SSO reduces password fatigue and shrinks the attack surface (fewer credentials to steal). Entra ID provides SSO across connected apps.
- **Multifactor authentication (MFA)** requires **two or more** verification factors from different categories: something you *know* (password), something you *have* (a phone or hardware token), and something you *are* (a fingerprint or face). MFA dramatically reduces the risk of compromised credentials, because a stolen password alone is not enough to sign in.

## Conditional Access

**Conditional Access** is an Entra ID feature that applies **policies** to sign-in attempts based on signals such as user, device, location, application, and real-time risk. For example, a policy might require MFA when a user signs in from an unfamiliar country, or block access from non-compliant devices. Conditional Access enforces the right controls automatically and is a key tool for implementing Zero Trust.

## Azure RBAC

**Azure Role-Based Access Control (RBAC)** is the **authorization** system for Azure resources. It grants permissions by assigning **roles** (such as *Owner*, *Contributor*, or *Reader*) to a **security principal** (user, group, or service) at a particular **scope** (Management Group, Subscription, Resource Group, or individual resource). Two important relationships:

- RBAC follows the **least-privilege** principle — grant only the access needed.
- Role assignments are **inherited down the management hierarchy**: a role granted at a Subscription applies to all Resource Groups and resources beneath it (mirroring the Management Group → Subscription → Resource Group → Resource structure).

## Zero Trust

**Zero Trust** is a security model built on the principle **"never trust, always verify."** It assumes breach and treats every request as though it originates from an untrusted network, regardless of where it comes from. Its guiding principles are: **verify explicitly** (authenticate and authorize on all available signals), **use least-privilege access**, and **assume breach** (minimize blast radius, verify end to end). Conditional Access, MFA, and RBAC are practical building blocks of a Zero Trust architecture.

## Defense in depth

**Defense in depth** is a strategy that uses **multiple layers** of security so that if one layer is breached, others still protect the asset. The layers are commonly described as: **physical security → identity and access → perimeter → network → compute → application → data**, with the **data** layer at the center. No single control is relied upon; the layers work together.

## Microsoft Defender for Cloud

**Microsoft Defender for Cloud** is a **cloud security posture management (CSPM)** and **cloud workload protection (CWPP)** platform. It continuously assesses your Azure, hybrid, and multicloud resources, provides a **Secure Score** that measures your security posture, gives recommendations to harden resources, and detects and alerts on threats. It helps implement defense in depth by surfacing weaknesses across all layers.

## Governance tools

### Azure Policy

**Azure Policy** enforces organizational standards and assesses compliance at scale. You define **policies** (rules) — for example, "only allow resources in West Europe" or "require a tag on every resource" — and Azure Policy evaluates resources against them, flagging or blocking non-compliant deployments. Like RBAC, policies are **inherited down** the management hierarchy, so a policy assigned to a Management Group governs all subscriptions beneath it. Whereas RBAC controls *who can do what*, Azure Policy controls *what the resources themselves are allowed to be*.

### Resource locks

**Resource locks** protect against accidental deletion or modification. There are two lock levels:

- **CanNotDelete** — authorized users can still read and modify a resource, but cannot delete it.
- **ReadOnly** — users can read a resource but cannot modify or delete it.

Locks can be applied at the Subscription, Resource Group, or resource level and are inherited by child resources. Because a lock overrides RBAC permissions, even an Owner must remove the lock before performing the blocked action.

### Service Trust Portal

The **Service Trust Portal** is a Microsoft website that publishes **compliance and audit information** — independent audit reports (such as SOC and ISO certifications), data protection documentation, and compliance guides. It helps customers understand how Microsoft protects data and meets regulatory standards, supporting their own governance and compliance efforts.

### Microsoft Purview

**Microsoft Purview** is a family of **data governance, compliance, and risk** solutions. It helps organizations **discover, classify, catalog, and protect** data across on-premises, multicloud, and SaaS environments — for example, mapping where sensitive data lives (a data map), applying sensitivity labels, and managing data-related compliance obligations. Purview addresses governance *of the data itself*, complementing Azure Policy's governance of resources.

**Relationship summary:** **Entra ID** authenticates identities; **Conditional Access** and **MFA** strengthen those sign-ins; **Azure RBAC** authorizes what identities can do; **Azure Policy** and **resource locks** control the resources; **Defender for Cloud**, **Zero Trust**, and **defense in depth** provide layered protection; and the **Service Trust Portal** and **Microsoft Purview** support compliance and data governance.
