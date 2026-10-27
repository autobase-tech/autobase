# Ansible Role: cloud_resources

Provision the PostgreSQL cluster infrastructure in public clouds (AWS, GCP, Azure, DigitalOcean, Hetzner). The role can:

- Create/delete servers (count, size, image, region), distributed across availability zones (AWS, GCP, Azure)
- Configure private networking/VPC/VNet and firewalls/Security Groups
- Optionally create Load Balancers (AWS NLB, GCP TCP Proxy, Azure LB, DigitalOcean LB, Hetzner LB)
- Optionally create object storage for backups (S3/GCS/Azure Blob/Spaces/Hetzner Object Storage)
- Generate in-memory inventory (postgres_cluster, master/replica, etcd_cluster/consul_instances).

## Requirements

- Collections on control host:
  - amazon.aws, community.aws
  - google.cloud
  - azure.azcollection
  - community.digitalocean
  - hetzner.hcloud
- Credentials via environment variables:
  - AWS: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
  - GCP: `GCP_SERVICE_ACCOUNT_CONTENTS` (JSON or base64)
  - Azure: `AZURE_SUBSCRIPTION_ID`, `AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_TENANT`
  - DigitalOcean: `DO_API_TOKEN`
  - Hetzner: `HCLOUD_API_TOKEN`

Collection versions are specified in [requirements.yml](../../requirements.yml).

## Variables

The zone placement variables apply to AWS, GCP and Azure; see [Availability zones](#availability-zones) for placement rules and examples.

| Variable | Type | Default | Description |
|---------|------|---------|-------------|
| cloud_provider | string | "" | Specifies the Cloud provider for server creation. Available options: 'aws', 'gcp', 'azure', 'digitalocean', 'hetzner' |
| cloud_backup_provider | string | cloud_provider | Specifies the Cloud provider for backup storage independently of the server provider. |
| cloud_provider_tags | dict | Managed: autobase | Custom tags for supported resources; see [Custom resource tags](#custom-resource-tags). |
| cloud_backup_provider_tags | dict | cloud_provider_tags | Tags for backup storage resources. An explicit dictionary replaces the inherited tags. |
| state | string | present | present to create, absent to delete |
| server_count | int | 3 | Number of servers in the cluster |
| server_name | string | {{ patroni_cluster_name }}-pgnode | Will be automatically named with suffixes 01, 02, 03, etc. |
| server_type | string | "" | Instance/VM size (required) |
| server_image | string | "" | OS image. For Azure, use variables 'azure_vm_image_offer', 'azure_vm_image_publisher', 'azure_vm_image_sku', 'azure_vm_image_version' instead of 'server_image' variable |
| server_location | string | "" | Region/zone (required) |
| server_network | string | "" | Existing network/subnet/VPC. If provided, the server will be added to this network (needs to be created beforehand) |
| server_spot | bool | false | Spot/preemptible where supported. Applicable for AWS, GCP, Azure |
| server_public_ip | bool | true | Assign public IPs to servers |
| server_zones_count | int | 3 | Required number of zones to select. Set to `1` for single-zone placement. AWS, GCP and Azure only. |
| server_zones | list | [] | Preferred zones in priority order. If empty, zones are selected automatically. AWS, GCP and Azure only. |
| server_placement | dict | {} | Explicit zone overrides for new servers, keyed by server name. AWS, GCP and Azure only. |
| volume_type | string | "" | Data disk type. Set to `local` to use the system disk and skip creating an external data disk. Defaults: 'gp3' for AWS, 'pd-ssd' for GCP, 'StandardSSD_LRS' for Azure |
| volume_size | int | 100 | Data disk size (GB). Set to `0` to use the system disk; this is equivalent to `volume_type: local` |
| system_volume_type | string | "" | System disk type. Defaults: 'gp3' for AWS, 'pd-ssd' for GCP, 'StandardSSD_LRS' for Azure |
| system_volume_size | int | 100 | System disk size (GB) |
| ssh_key_name | string | "" | Name of an SSH key to use from the cloud. If not provided, all available keys will be added (DigitalOcean, Hetzner) |
| ssh_key_content | string | "" | If provided, the public key content will be added to the cloud (directly to the server for GCP) |
| cloud_firewall | bool | true | Manage firewall/Security Groups |
| ssh_public_access | bool | true | Allow public ssh access (required for deployment from the public network). Applicable if server_public_ip is set to true |
| ssh_public_allowed_ips | string | "" | Comma-separated CIDRs for SSH (empty = 0.0.0.0/0,::/0) |
| netdata_public_access | bool | false | Allow public Netdata (if 'netdata_install' is 'true') |
| netdata_public_allowed_ips | string | "" | Comma-separated CIDRs for Netdata |
| database_public_access | bool | false | Allow public DB access |
| database_public_allowed_ips | string | "" | Comma-separated CIDRs for DB |
| cloud_load_balancer | bool | true | Create cloud Load Balancers (master switch) |
| cloud_load_balancer_replica | bool | true | Create a Load Balancer for all replicas |
| cloud_load_balancer_replica_sync | bool | false | Create a Load Balancer for synchronous replicas (requires synchronous_mode) |
| cloud_load_balancer_replica_async | bool | false | Create a Load Balancer for asynchronous replicas (requires synchronous_mode) |
| aws_nlb_client_routing_policy | string | availability_zone_affinity | NLB DNS client routing policy: `availability_zone_affinity`, `partial_availability_zone_affinity` or `any_availability_zone` |
| aws_nlb_replica_cross_zone | bool | false | Cross-zone load balancing for replica NLBs (replica, sync, async). Always enabled for the primary NLB |
| aws_s3_bucket_create | bool | true | Create S3 bucket (if 'pgbackrest_install' or 'wal_g_install' is 'true') |
| aws_s3_bucket_name | string | {{ patroni_cluster_name }}-backup | Bucket name |
| aws_s3_bucket_region | string | {{ server_location }} | Bucket region |
| aws_s3_bucket_object_lock_enabled | bool | false | Enable S3 Object Lock |
| aws_s3_bucket_encryption | string | AES256 | Server-side encryption ("AES256","aws:kms") |
| aws_s3_bucket_block_public_acls | bool | true | BlockPublicAcls |
| aws_s3_bucket_ignore_public_acls | bool | true | IgnorePublicAcls |
| aws_s3_bucket_absent | bool | false | Allow delete bucket on state=absent |
| gcp_bucket_create | bool | true | Create GCS bucket (if 'pgbackrest_install' or 'wal_g_install' is 'true') |
| gcp_bucket_name | string | {{ patroni_cluster_name }}-backup | Storage bucket name |
| gcp_bucket_storage_class | string | MULTI_REGIONAL | Storage bucket class |
| gcp_bucket_default_object_acl | string | projectPrivate | Default object ACL |
| gcp_bucket_absent | bool | false | Allow delete bucket on state=absent |
| azure_blob_storage_create | bool | true | Create Azure Blob container (if 'pgbackrest_install' or 'wal_g_install' is 'true') |
| azure_backup_location | string | {{ server_location }} | Azure region for backup storage. Can differ from the server region. |
| azure_blob_storage_name | string | {{ patroni_cluster_name }}-backup | Name of a blob container within the storage account |
| azure_blob_storage_blob_type | string | block | Type of blob object. Values include: block, page |
| azure_blob_storage_account_name | string | {{ patroni_cluster_name }} | Storage account name. Must be between 3 and 24 characters in length and use numbers and lower-case letters only |
| azure_blob_storage_account_type | string | Standard_RAGRS | Type of storage account. Values include: Standard_LRS, Standard_GRS, Standard_RAGRS, Standard_ZRS, Standard_RAGZRS, Standard_GZRS, Premium_LRS, Premium_ZRS |
| azure_blob_storage_account_kind | string | StorageV2 | The kind of storage. Values include: StorageV2, BlockBlobStorage, FileStorage |
| azure_blob_storage_account_access_tier | string | Hot | The access tier for blob data in this storage account |
| azure_blob_storage_account_public_network_access | string | Enabled | Allow public network access to Storage Account to create Blob Storage container |
| azure_blob_storage_account_allow_blob_public_access | bool | false | Allow anonymous blob access |
| azure_blob_storage_absent | bool | false | Allow delete Azure Blob Storage on state=absent |
| digital_ocean_spaces_create | bool | true | Create Spaces bucket (if 'pgbackrest_install' or 'wal_g_install' is 'true') |
| digital_ocean_spaces_name | string | {{ patroni_cluster_name }}-backup | Spaces name |
| digital_ocean_spaces_region | string | nyc3 | Spaces region |
| digital_ocean_spaces_absent | bool | false | Allow delete Spaces on state=absent |
| hetzner_object_storage_create | bool | true | Create Hetzner Object Storage (if 'pgbackrest_install' or 'wal_g_install' is 'true') |
| hetzner_object_storage_name | string | {{ patroni_cluster_name }}-backup | Bucket name |
| hetzner_object_storage_region | string | {{ server_location }} | Region |
| hetzner_object_storage_endpoint | string | https://{{ hetzner_object_storage_region }}.your-objectstorage.com | S3 endpoint |
| hetzner_object_storage_access_key | string | "" | Object Storage ACCESS KEY (required) |
| hetzner_object_storage_secret_key | string | "" | Object Storage SECRET KEY (required) |
| hetzner_object_storage_absent | bool | false | Allow delete Object Storage on state=absent |

Set `cloud_backup_provider` when backup storage should be provisioned in a different cloud than the database servers. In that case, also provide the credentials and region-related variables required by the selected backup provider (for example, `azure_backup_location` for Azure). The `server_location` value continues to describe the server provider and is not translated between clouds.

### Provider-specific variables

| Provider | Variable | Type | Default | Description |
|----------|----------|------|---------|-------------|
| AWS | aws_subnet_ids | list | [] | Subnets for servers in a custom VPC, one per Availability Zone (a list or a comma-separated string). Required for multi-AZ in a custom VPC. If specified, `server_network` is ignored. |
| AWS | aws_security_group_ids | list | [] | Additional Security Group IDs to attach to AWS EC2 instances. |
| AWS | aws_ec2_spot_instance | string | "" | Fallback for `server_spot`. |
| AWS | aws_ebs_encrypted | bool | true | Encrypt AWS EBS system and data volumes. |
| AWS | aws_ec2_imds_v2_required | bool | true | Require IMDSv2 (session tokens) for the instance metadata service on new EC2 instances (IMDSv1 disabled). Not applied to Spot instances. |
| AWS | aws_ebs_kms_key_id | string | "" | Customer-managed AWS KMS key ID or ARN for EBS encryption. If empty, AWS uses the default EBS encryption key. |
| GCP | gcp_project | string | "" | Falls back to `project_id` from the service account credentials. |
| GCP | gcp_subnetwork | string | "" | Name of a private subnetwork in `server_network` and the selected region. Defaults to the existing VMs' subnetwork, or the only private subnetwork in the region. Required when multiple private subnetworks exist and there are no existing VMs. |
| GCP | gcp_compute_instance_preemptible | bool | false | Fallback for `server_spot`. |
| GCP | gcp_compute_health_check_interval_sec | int | "provider default" | Interval tuning for health checks. |
| GCP | gcp_compute_health_check_check_timeout_sec | int | "provider default" | Timeout tuning for health checks. |
| GCP | gcp_compute_health_check_unhealthy_threshold | int | "provider default" | Unhealthy threshold tuning for health checks. |
| GCP | gcp_compute_health_check_healthy_threshold | int | "provider default" | Healthy threshold tuning for health checks. |
| GCP | gcp_compute_backend_service_timeout_sec | int | "provider default" | Backend service timeout tuning. |
| GCP | gcp_compute_backend_service_log_enable | bool | false | Enables backend service logging. |
| DigitalOcean | digital_ocean_vpc_name | string | "" | Custom VPC name if creating one. |
| DigitalOcean | digital_ocean_load_balancer_size | string | "lb-medium" | Default for `server_location` values `ams2`, `nyc2`, `sfo1`. |
| DigitalOcean | digital_ocean_load_balancer_size_unit | int | 3 | Default when `server_location` is not in `['ams2', 'nyc2', 'sfo1']`. |
| DigitalOcean | digital_ocean_load_balancer_port | int | `pgbouncer_listen_port` | Load balancer port. |
| DigitalOcean | digital_ocean_load_balancer_target_port | int | `pgbouncer_listen_port` | Target port for the load balancer. |
| Azure | azure_resource_group | string | "" | Resource group name. |
| Azure | azure_virtual_network | string | postgres-cluster-network | VNet name. |
| Azure | azure_subnet | string | postgres-cluster-subnet | Subnet name. |
| Azure | azure_virtual_network_prefix | string | 10.0.0.0/16 | VNet CIDR. |
| Azure | azure_subnet_prefix | string | 10.0.1.0/24 | Subnet CIDR. |
| Azure | azure_admin_username | string | azureadmin | Administrative username for the VM. |
| Azure | azure_vm_image_offer | string | "" | Image offer. |
| Azure | azure_vm_image_publisher | string | "" | Image publisher. |
| Azure | azure_vm_image_sku | string | "" | Image SKU. |
| Azure | azure_vm_image_version | string | "" | Image version. |
| Hetzner | hetzner_load_balancer_type | string | lb21 | Load balancer type. |
| Hetzner | hetzner_placement_group | bool | true | Place cluster servers in one spread placement group, on different physical hosts. Maximum 10 servers. |
| Hetzner | hcloud_network_name | string | postgres-cluster-network-<zone> | Network name if creating one. |
| Hetzner | hcloud_network_ip_range | string | 10.0.0.0/16 | Network CIDR. |
| Hetzner | hcloud_subnetwork_ip_range | string | 10.0.1.0/24 | Subnet CIDR. |

### Availability zones

AWS, GCP and Azure support placement across availability zones. The role selects `server_zones_count` zones (3 by default).
Surviving a zone failure also requires a healthy database replica and a DCS quorum; see [DCS cluster](#dcs-cluster).

DigitalOcean is not included in the role's multi-AZ placement because its managed load balancers cannot provide a PostgreSQL TCP endpoint across datacenters. [Regional load balancers](https://docs.digitalocean.com/products/networking/load-balancers/details/features/) serve a single datacenter, while [global load balancers](https://docs.digitalocean.com/products/networking/load-balancers/how-to/manage-global-load-balancers/#forwarding-rules) support only HTTP(S) forwarding; TCP is supported for health checks only.

Hetzner Cloud does not expose availability zones within its [locations](https://docs.hetzner.com/cloud/general/locations/) and is not included in multi-AZ placement. [Spread placement groups](#hetzner-placement-groups) separate servers across physical hosts but do not provide availability-zone isolation.

Cross-zone replication adds network latency, including to commits when `synchronous_mode` is enabled.
Consider your provider's inter-zone traffic costs when choosing a placement. Set `server_zones_count: 1` for a single-zone cluster.

#### Placement rules

The role selects zones from `server_zones`, or from the provider's discovery results when this list is empty.
Within that list, zones already used by existing servers take priority; the first `server_zones_count` zones are selected.
Deployment fails if fewer zones are available than requested, including when `server_zones` limits the selection.
Single-zone placement must be explicitly enabled with `server_zones_count: 1`.

Each server (`<server_name>01`, `<server_name>02`, ...) is placed as follows:

1. An existing server keeps its placement, even if `server_placement` requests another zone.
2. A new server listed in `server_placement` uses that zone, even if it is outside the selected set.
3. Other new servers use the selected zone with the fewest servers; ties follow the zone order.

Existing Azure VMs created without a zone keep their regional placement. Their actual zone is unknown.
To change an existing server's placement, follow [Moving an existing cluster to multiple zones](#moving-an-existing-cluster-to-multiple-zones).

#### Zones and networks

**AWS**

- With `aws_subnet_ids`, zones are taken from those subnets in the supplied order, with one subnet per zone in the same VPC.
- With only `server_network`, its subnet determines a single zone; set `server_zones_count: 1`.
- With neither, the default VPC's default subnets are used in alphabetical zone order.

**GCP**

- With a region in `server_location` (for example, `europe-west1`), zones with status `UP` that support `server_type` are discovered in alphabetical order.
- An explicit zone (for example, `europe-west1-b`) restricts new servers to that zone and requires `server_zones_count: 1`.
- `server_network` is the VPC network name (defaults to `default`). All VMs share one private regional subnetwork; use `gcp_subnetwork` to select it explicitly.

**Azure**

- `server_location` is a region (for example, `westeurope`). Logical zone IDs are `"1"`, `"2"`, `"3"` within the subscription; numeric YAML values are also accepted.
- Zones are discovered for `server_type`, excluding subscription restrictions. Discovery does not reserve allocation or Spot capacity.
- All VMs share one regional VNet and `azure_subnet`. Existing VMs must also use this subnet.
- If the VM SKU has no zonal support, regional placement requires `server_zones_count: 1` and empty `server_zones` and `server_placement`.
  The role warns that regional placement does not protect against a zone failure. Subscription restrictions cause an error.

#### Examples

AWS with a custom VPC:

```yaml
cloud_provider: aws
server_zones_count: 3
aws_subnet_ids:
  - subnet-0a1b2c3d4e5f60001 # us-east-1a
  - subnet-0a1b2c3d4e5f60002 # us-east-1b
  - subnet-0a1b2c3d4e5f60003 # us-east-1c
server_placement: # optional
  postgres-cluster-pgnode01: us-east-1b
```

GCP with preferred zones:

```yaml
cloud_provider: gcp
server_location: europe-west1
server_zones: # optional
  - europe-west1-b
  - europe-west1-c
  - europe-west1-d
```

Azure with preferred zones and a server override:

```yaml
cloud_provider: azure
server_location: westeurope
server_type: Standard_D4s_v5
server_zones: ["1", "2", "3"] # optional
server_placement: # optional
  postgres-cluster-pgnode01: "2"
```

#### DCS cluster

Unless `dcs_exists: true`, etcd or Consul runs on up to the first 7 database servers in inventory order, with existing servers before new ones.
To retain quorum after any single zone fails, the DCS must span at least 3 zones and keep a majority of its members outside each zone.
For example, 4 DCS members distributed 2/1/1 lose quorum if the zone with 2 members fails.

The role rejects an unsafe placement for a new multi-zone cluster and warns when scaling or changing an existing cluster.
This validation is skipped for single-zone placement and a dedicated DCS (`dcs_exists: true`).
If a DCS member is an Azure regional VM without a known zone, the role warns that zone-failure tolerance cannot be verified.
In a cluster with more than 7 database servers, a replacement is ordered after the existing servers and does not become a DCS member.

For production, a dedicated etcd cluster with one member in each of 3 zones (`dcs_exists: true` and `patroni_etcd_hosts`)
keeps DCS quorum independent of database server count and placement.

#### Load balancers

##### AWS Network Load Balancer

NLBs are enabled in the zones of all servers. When new servers are added in a new zone, the zone is added to the existing NLBs online:
their DNS names and existing IP addresses are kept.

With `aws_nlb_client_routing_policy: availability_zone_affinity` (default), clients that use the Route 53 Resolver of the VPC
resolve the NLB IP address in their own zone, if it has a healthy target.

- Primary NLB: cross-zone load balancing is always enabled, so the NLB node in any zone forwards connections to the primary
  right after a failover, without waiting for DNS changes.
- Replica NLBs: with `aws_nlb_replica_cross_zone: false` (default), reads stay in the client's zone when it has a healthy replica.
  The NLB node in a zone forwards connections only to targets in its own zone. If the zone has no healthy replica
  (for example, the zone of the primary), its IP address is removed from DNS and clients resolve the NLB in other zones.
  However, the NLB node in that zone fails open and forwards connections to all targets in its zone, including the primary.
  After a switchover, clients that still use a cached DNS record (TTL 60 seconds) or keep connecting to that IP address
  reach the primary through the replica endpoint until the record is refreshed, and replicas may receive uneven load.
  To make sure that such connections never use the primary, connect with `target_session_attrs=standby` (or `prefer-standby`),
  or set `aws_nlb_replica_cross_zone: true` to distribute connections across replicas in all zones.

##### Azure Load Balancer

In regions with three availability zones, new Standard public IPs (for VMs and load balancers) and internal load balancer frontends use zone redundancy.
Frontend placement uses the region's zones independently of VM SKU availability. Internal frontends use `azure_subnet`.
Each enabled primary/replica/sync/async endpoint uses the corresponding Patroni health probe.
Backend pool settings and members are read before load balancer updates and reapplied afterwards; scaling adds the new servers' addresses.

Existing IP addresses and frontend zone settings are preserved. The role warns about zonal frontends/public IPs and internal frontends without explicit zone redundancy.
Migrate these frontends separately before relying on them during a zone failure; public IP zone settings cannot be changed in place.
Changing `database_public_access` for an existing load balancer also requires a separate frontend migration.
A Standard public IP without explicit zones may already be zone redundant and does not trigger this warning.

#### Moving an existing cluster to multiple zones

Configure the target zones with `server_zones_count`, optionally `server_zones` and `server_placement`, while keeping the existing cluster network:

- AWS: include the current and target zones' subnets in `aws_subnet_ids`.
- GCP: use a region in `server_location` and keep the shared regional subnetwork.
- Azure: ensure any reused disks and zonal public IPs are compatible with the target zone. Create a new zone-redundant public IP if needed.

Replace replicas one at a time:

1. Remove a replica using `remove_node.yml`, delete its cloud VM and wait for deletion to finish (`terminated` for EC2).
2. Add it again using `add_node.yml` with the same desired `server_count`. The role applies the new placement and updates the load balancers.
3. Repeat for the remaining replicas. Switch over to a replica before replacing the primary.

### Hetzner placement groups

By default, all Hetzner cluster servers are assigned to a `spread` placement group named `<patroni_cluster_name>-<server_location>`.
The group is reused when scaling the cluster and deleted after the servers when `state: absent`.
Hetzner guarantees that servers in the group run on different physical hosts; this does not provide availability-zone isolation.
See the [Hetzner placement group FAQ](https://docs.hetzner.com/cloud/placement-groups/faq/).

A spread group supports at most 10 servers. When `hetzner_placement_group` is enabled, deployment fails if `server_count` exceeds this limit.
Set `hetzner_placement_group: false` to skip placement group management during provisioning, without guaranteed host separation.
This setting leaves existing server placement unchanged; cluster deletion still removes the managed group.

For example, to grow a cluster from 10 to 11 servers:

```yaml
server_count: 11
hetzner_placement_group: false
```

The original 10 servers remain in their group, while the new server is created without a placement group.
Keep the setting disabled on subsequent runs while the cluster exceeds 10 servers.

Existing servers outside the group must be powered off before they can be added.
The role fails if any such server is running and never forces a shutdown or moves a running node between groups.
For an existing cluster, migrate nodes individually during maintenance using Hetzner's controls, preserving a healthy primary and DCS quorum,
then rerun provisioning once all existing nodes belong to the group. Alternatively, disable the feature to retain their current placement.

## Custom resource tags

```yaml
cloud_provider_tags:
  Managed: autobase
  Environment: production
  Team: platform
cloud_backup_provider_tags: # Optional; inherits cloud_provider_tags when omitted
  Managed: autobase
  Environment: production
  Team: platform
  Purpose: backup
```

Custom tags are applied when servers are created. Existing servers retain their tags when `cloud_provider_tags` changes.
Other resources managed by create-or-update tasks, such as networks, firewalls, NICs and load balancers, may have their tags reconciled on later runs.
AWS Spot instances are an exception: the Spot request creates the EC2 instance, so the instance can only be named and tagged afterward with the modules currently used by this role.

Autobase's `Name` (EC2 instances) and `Cluster` (`cluster` for GCP) values take precedence over conflicting custom values.
For GCP, Autobase converts label keys and values to lowercase before applying them to VM instances and backup buckets.
GCP requires label keys and values to use lowercase letters, numbers, underscores or hyphens. Keys must start with a lowercase letter.
The DigitalOcean cluster tag and GCP network tags remain unchanged because firewalls and load balancers use them to select servers.
Use strings for all keys and values (quote numeric values), and follow the selected provider's naming and count limits.
When backup storage uses a different provider, inherited tags must also satisfy that provider's restrictions.

| Provider | Resources tagged by this role | Exceptions |
|----------|-------------------------------|------------|
| AWS | SSH keys created by the role, security groups, EC2 instances, Spot requests, EBS volumes created with regular EC2 instances, NLB, NLB target groups, S3 buckets | ENIs are not tagged. EBS volumes attached to Spot instances may remain untagged. Existing VPCs/subnets and service-managed load balancer child resources are not modified. |
| GCP | VM instances and GCS buckets | System and data disks are not labeled. The Ansible modules used for global static load balancer IP addresses, forwarding rules, backend services, health checks, proxies, unmanaged instance groups and VPC firewall rules do not expose labels. Existing networks/subnets are not modified. |
| Azure | Resource groups, VNets created by the role, public IPs, security groups, NICs, VMs, load balancers and backup storage accounts | OS and data managed disks are not tagged. Subnets, load balancer child configurations and Blob containers do not support resource tags. Tags on a resource group are not inherited automatically. |
| DigitalOcean | Droplets | Data volumes cannot be tagged through the collection module. VPCs, SSH keys, firewalls, load balancers and Spaces buckets do not support resource tagging. Root disks and public IPs belong to the Droplet. |
| Hetzner Cloud | SSH keys created by the role, networks created by the role, firewalls, servers, volumes and load balancers | Primary IPs are not labeled. Subnetworks and load balancer services/targets are child configurations without labels. Root disks belong to the server. Object Storage bucket tagging is unsupported. |

## Dependencies

This role depends on:

- `vitabaks.autobase.common` - Provides common variables and configurations
