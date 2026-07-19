# Azure Storage

## The Azure Storage account

An **Azure Storage account** is the top-level container that groups a set of Azure Storage data services under a single namespace and set of settings. When you create a Storage account you choose its **redundancy option**, its **region**, and its **performance tier**. A single Storage account can hold several distinct data services, each addressing a different data shape:

- **Azure Blob Storage** — for unstructured object data.
- **Azure Files** — for managed file shares.
- **Azure Queue Storage** — for messaging between application components.
- **Azure Table Storage** — for structured NoSQL key-value data.

The Storage account provides a unique endpoint (URL) for each of these services and applies account-wide security, encryption at rest, and access controls.

## Azure Blob Storage and access tiers

**Azure Blob Storage** ("Blob" = Binary Large Object) is object storage optimized for massive amounts of **unstructured data** such as images, video, backups, logs, and documents. Blobs are organized into **containers** within a Storage account. Blob Storage is ideal for serving files to browsers, streaming media, and storing data for analysis.

Blob Storage offers **access tiers** that let you balance storage cost against access cost based on how often data is read:

- **Hot tier** — highest storage cost, lowest access cost. For data accessed frequently.
- **Cool tier** — lower storage cost, higher access cost; intended for data accessed infrequently and stored for at least 30 days.
- **Cold tier** — even lower storage cost than cool, higher access cost; for rarely accessed data stored at least 90 days, but still online.
- **Archive tier** — lowest storage cost, highest access cost and latency. Data is offline and must be **rehydrated** (moved back to an online tier) before it can be read, which can take hours. For long-term retention such as compliance archives.

**Lifecycle management** policies can automatically move blobs between tiers (for example, Hot → Cool → Archive) as they age, optimizing cost without manual intervention.

## Azure Files

**Azure Files** offers fully managed **file shares** in the cloud, accessible over the industry-standard **SMB** and **NFS** protocols. Because Azure Files shares can be mounted like a network drive by cloud or on-premises machines simultaneously, they are useful for replacing or supplementing on-premises file servers ("lift and shift" of file shares) and for sharing configuration or application data across multiple machines.

## Azure Queue Storage

**Azure Queue Storage** stores large numbers of messages that can be accessed from anywhere. It is used to **decouple** application components: one component adds messages to a queue, and another reads and processes them asynchronously. This supports building scalable, resilient applications, and it pairs naturally with **Azure Functions**, which can trigger on new queue messages.

## Azure Table Storage

**Azure Table Storage** is a **NoSQL** key-value store for structured, non-relational data. It stores large amounts of data in a schemaless design, is fast and cost-effective, and is suited to data that does not require complex joins, foreign keys, or stored procedures — such as user profiles, device information, or catalogs.

## Disk storage

**Azure managed disks** are block-level storage volumes attached to Azure Virtual Machines, functioning as the VM's virtual hard drives. Azure manages the underlying storage. Disks come in tiers — **Standard HDD, Standard SSD, Premium SSD, and Ultra Disk** — trading cost against performance (IOPS and throughput). Managed disks integrate with Availability Sets and Zones for resilience.

## Redundancy options

Azure Storage always keeps multiple copies of your data to protect against hardware failures. The **redundancy option** you choose determines how many copies exist and how far apart they are:

- **Locally Redundant Storage (LRS)** — three copies within a single datacenter in one region. Lowest cost; protects against server and rack failures but not a datacenter-wide disaster.
- **Zone-Redundant Storage (ZRS)** — copies spread across **three Availability Zones** within a single region. Protects against the failure of an entire datacenter/zone.
- **Geo-Redundant Storage (GRS)** — LRS in the primary region **plus** an asynchronous copy to a second, paired region (again as LRS). Protects against a full regional outage. The secondary copy is not readable unless a failover occurs.
- **Geo-Zone-Redundant Storage (GZRS)** — combines ZRS in the primary region (three zones) with a geo-replicated copy in the paired region. Offers the highest durability, protecting against both zone and regional failures.

Read-access variants (**RA-GRS** and **RA-GZRS**) additionally allow reading from the secondary region at any time. The general relationship: **LRS < ZRS < GRS < GZRS** in terms of durability and cost, moving from single-datacenter to multi-zone to multi-region protection.

## Data migration tools

Azure provides several tools to move data into (and within) Azure Storage:

- **AzCopy** — a command-line utility for copying blobs and files to and from Storage accounts, including between accounts and across regions. Good for scripted, ongoing, or bulk transfers over the network.
- **Azure Migrate** — a centralized hub and service for discovering, assessing, and migrating on-premises **servers, databases, web apps, and data** to Azure. It provides assessment (readiness, sizing, cost estimates) and orchestrates the migration itself. Azure Migrate coordinates other tools rather than just copying files.
- **Azure Data Box** — a **physical appliance** that Microsoft ships to your site. You copy large volumes of data (terabytes) onto the device and ship it back to a datacenter, where the data is uploaded. Data Box is the right choice when network bandwidth is too limited or too slow to transfer the data online in a reasonable time.

**Relationship summary:** Use **AzCopy** for online, network-based transfers; **Azure Migrate** to assess and move whole workloads; and **Azure Data Box** for offline, physical transfer of very large datasets.
