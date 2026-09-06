# Ansible Role: cloud_resources

Provision the PostgreSQL cluster infrastructure in public clouds (AWS, GCP, Azure, DigitalOcean, Hetzner). The role can:
- Create/delete servers (count, size, image, region)
- Configure private networking/VPC/VNet and firewalls/Security Groups
- Optionally create Load Balancers (AWS NLB/CLB, GCP TCP Proxy, Azure LB, DO LB, Hetzner LB)
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

## Variables

| Variable | Type | Default | Description |
|---------|------|---------|-------------|
| cloud_provider | string | "" | Specifies the Cloud provider for server creation. Available options: 'aws', 'gcp', 'azure', 'digitalocean', 'hetzner' |
| cloud_backup_provider | string | cloud_provider | Specifies the Cloud provider for backup storage independently of the server provider. |
| cloud_provider_tags | dict | managed-by: autobase | Custom resource tags (string keys and values). |
| cloud_backup_provider_tags | dict | cloud_provider_tags | Custom backup storage tags. An explicit dictionary replaces the inherited custom tags. |
| state | string | present | present to create, absent to delete |
| server_count | int | 3 | Number of servers in the cluster |
| server_name | string | {{ patroni_cluster_name }}-pgnode | Will be automatically named with suffixes 01, 02, 03, etc. |
| server_type | string | "" | Instance/VM size (required) |
| server_image | string | "" | OS image. For Azure, use variables 'azure_vm_image_offer', 'azure_vm_image_publisher', 'azure_vm_image_sku', 'azure_vm_image_version' instead of 'server_image' variable |
| server_location | string | "" | Region/zone (required) |
| server_network | string | "" | Existing network/subnet/VPC. If provided, the server will be added to this network (needs to be created beforehand) |
| server_spot | bool | false | Spot/preemptible where supported. Applicable for AWS, GCP, Azure |
| server_public_ip | bool | true | Assign public IPs to servers |
| volume_type | string | "" | Data disk type. Set to `local` to use the system disk and skip creating an external data disk. Defaults: 'gp3' for AWS, 'pd-ssd' for GCP, 'StandardSSD_LRS' for Azure |
| volume_size | int | 100 | Data disk size (GB). Set to `0` to use the system disk; this is equivalent to `volume_type: local` |
| system_volume_type | string | "" | System disk type. Defaults: 'gp3' for AWS, 'pd-ssd' for GCP, 'StandardSSD_LRS' for Azure |
| system_volume_size | int | 100 | System disk size (GB) |
| ssh_key_name | string | "" | Name of the SSH key to be added to the server. Note: If not provided, all cloud available SSH keys will be added (applicable to DigitalOcean, Hetzner) |
| ssh_key_content | string | "" | If provided, the public key content will be added to the cloud (directly to the server for GCP) |
| cloud_firewall | bool | true | Manage firewall/Security Groups |
| ssh_public_access | bool | true | Allow public ssh access (required for deployment from the public network). Applicable if server_public_ip is set to true |
| ssh_public_allowed_ips | string | "" | Comma-separated CIDRs for SSH (empty = 0.0.0.0/0,::/0) |
| netdata_public_access | bool | true | Allow public Netdata (if 'netdata_install' is 'true') |
| netdata_public_allowed_ips | string | "" | Comma-separated CIDRs for Netdata |
| database_public_access | bool | false | Allow public DB access |
| database_public_allowed_ips | string | "" | Comma-separated CIDRs for DB |
| cloud_load_balancer | bool | true | Create a cloud Load Balancer |
| aws_load_balancer_type | string | nlb | 'nlb' = Network Load Balancer; 'clb' = Classic Load Balancer (previous generation) |
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

Set `cloud_backup_provider` when backup storage should be provisioned in a different cloud than the database servers.
In that case, also provide the credentials and region-related variables required by the selected backup provider (for example, `azure_backup_location` for Azure).
The `server_location` value continues to describe the server provider and is not translated between clouds.

#### Custom resource tags

```yaml
cloud_provider_tags:
  managed-by: autobase
  environment: production
  team: platform
cloud_backup_provider_tags: # Optional; inherits cloud_provider_tags when omitted
  managed-by: autobase
  environment: production
  team: platform
  purpose: backup
```

Run `cloud_resources.yml` again with `state: present` and the same cluster variables to apply tags to existing resources.
AWS and Azure add tags and update values without removing unrelated tags. GCP and Hetzner label dictionaries replace the existing labels on managed resources.
DigitalOcean adds missing `key:value` tags to Droplets. Changing a value adds a new `key:value` tag without removing the previous value. Custom keys cannot contain `:`.
Removing a key from the variables does not remove it on AWS, Azure or DigitalOcean.

Autobase's `Name` (EC2 instances) and `Cluster`/`cluster` values take precedence over conflicting custom values.
GCP requires label keys and values to use lowercase letters, numbers, underscores or hyphens. Keys must start with a lowercase letter.
The DigitalOcean cluster tag and GCP network tags remain unchanged because firewalls and load balancers use them to select servers.
Shared Azure resource groups and virtual networks, and shared Hetzner networks, receive the tags of the most recently processed cluster.
Use strings for all keys and values (quote numeric values), and follow the selected provider's naming and count limits.
When backup storage uses a different provider, inherited tags must also satisfy that provider's restrictions.

| Provider | Resources tagged by this role | Exceptions |
|----------|-------------------------------|------------|
| AWS | SSH keys created by the role, security groups, EC2 instances, Spot requests, attached EBS system/data volumes, instance network interfaces, CLB/NLB, NLB target groups, S3 buckets | Existing VPCs/subnets are reused and not modified. Service-managed load balancer child resources are not managed separately. |
| GCP | VM instances, system/data disks, GCS buckets | The Ansible modules used for global static load balancer IP addresses, forwarding rules, backend services, health checks, proxies, unmanaged instance groups and VPC firewall rules do not expose labels. Existing networks/subnets are not modified. |
| Azure | Resource groups, VNets created by the role, public IPs, security groups, NICs, VMs, OS/data managed disks, load balancers, backup storage accounts | Subnets, load balancer child configurations and Blob containers do not support resource tags. Tags on a resource group are not inherited automatically. |
| DigitalOcean | Droplets | The collection's tag module does not support data volumes. VPCs, SSH keys, firewalls, load balancers and Spaces buckets do not support resource tagging. Root disks and public IPs belong to the Droplet. |
| Hetzner | SSH keys created by the role, networks created by the role, firewalls, servers, Primary IPv4 addresses, volumes and load balancers | Subnetworks and load balancer services/targets are child configurations without labels. Root disks belong to the server. Object Storage bucket tagging is unsupported. |

### Provider-specific (optional) variables referenced in tasks

| Variable | Provider | Default/Notes |
|----------|----------|---------------|
| aws_ec2_spot_instance | AWS | Fallback for server_spot |
| gcp_project | GCP | Fallbacks to project_id from service account credentials |
| gcp_compute_instance_preemptible | GCP | Fallback for server_spot |
| gcp_compute_health_check_interval_sec, gcp_compute_health_check_check_timeout_sec, gcp_compute_health_check_unhealthy_threshold, gcp_compute_health_check_healthy_threshold | GCP | Interval/timeout/threshold tuning |
| gcp_compute_backend_service_timeout_sec, gcp_compute_backend_service_log_enable | GCP | LB Backend timeouts/logging |
| digital_ocean_vpc_name | DO | Custom VPC name if creating one |
| digital_ocean_load_balancer_size | DO | default('lb-medium') if server_location in ['ams2', 'nyc2', 'sfo1'] |
| digital_ocean_load_balancer_size_unit | DO | default(3) if server_location not in ['ams2', 'nyc2', 'sfo1'] |
| digital_ocean_load_balancer_port, digital_ocean_load_balancer_target_port | DO | LB port, default: pgbouncer_listen_port |
| azure_resource_group | Azure | Resource group name |
| azure_virtual_network, azure_subnet | Azure | VNet/Subnet names, default: postgres-cluster-network/postgres-cluster-subnet |
| azure_virtual_network_prefix, azure_subnet_prefix | Azure | CIDRs, default: '10.0.0.0/16'/'10.0.1.0/24' |
| azure_admin_username | Azure | Default: azureadmin |
| azure_vm_image_offer, azure_vm_image_publisher, azure_vm_image_sku, azure_vm_image_version | Azure | Image reference |
| hetzner_load_balancer_type | Hetzner | Default: lb21 |
| hcloud_network_name | Hetzner | Network name if creating, default('postgres-cluster-network-' + target_network_zone) |
| hcloud_network_ip_range, hcloud_subnetwork_ip_range | Hetzner | CIDRs, default: '10.0.0.0/16'/'10.0.1.0/24' |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
