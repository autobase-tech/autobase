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
| cloud_provider_tags | dict | managed-by: autobase | Custom tags requested when supported cloud resources are provisioned. Existing compute resources are not retagged on later runs. Keys and values must be strings. |
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
| cloud_load_balancer | bool | true | Create cloud Load Balancers (master switch) |
| cloud_load_balancer_replica | bool | true | Create a Load Balancer for all replicas |
| cloud_load_balancer_replica_sync | bool | false | Create a Load Balancer for synchronous replicas (requires synchronous_mode) |
| cloud_load_balancer_replica_async | bool | false | Create a Load Balancer for asynchronous replicas (requires synchronous_mode) |
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

Set `cloud_backup_provider` when backup storage should be provisioned in a different cloud than the database servers. In that case, also provide the credentials and region-related variables required by the selected backup provider (for example, `azure_backup_location` for Azure). The `server_location` value continues to describe the server provider and is not translated between clouds.

### Provider-specific variables

Provider-specific (optional) variables referenced in tasks

| Provider | Variable | Type | Default | Description |
|----------|----------|------|---------|-------------|
| AWS | aws_security_group_ids | list | [] | Additional Security Group IDs to attach to AWS EC2 instances. |
| AWS | aws_ec2_spot_instance | string | "" | Fallback for `server_spot`. |
| AWS | aws_ebs_encrypted | bool | true | Encrypt AWS EBS system and data volumes. |
| AWS | aws_ebs_kms_key_id | string | "" | Customer-managed AWS KMS key ID or ARN for EBS encryption. If empty, AWS uses the default EBS encryption key. |
| GCP | gcp_project | string | "" | Falls back to `project_id` from the service account credentials. |
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
| Hetzner | hcloud_network_name | string | postgres-cluster-network-<zone> | Network name if creating one. |
| Hetzner | hcloud_network_ip_range | string | 10.0.0.0/16 | Network CIDR. |
| Hetzner | hcloud_subnetwork_ip_range | string | 10.0.1.0/24 | Subnet CIDR. |

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

Autobase passes custom tags through provider modules while provisioning resources.
It does not run a separate tagging pass for existing compute resources or their attached child resources.
Changing `cloud_provider_tags` therefore does not retag existing VM instances, servers or Droplets.
Standalone resources managed by create-or-update tasks, such as networks, firewalls and load balancers, may still have their tags reconciled by the provider module.
Attached resources that the provider module cannot tag as part of their parent resource's creation remain untagged.
AWS Spot instances are an exception: the Spot request creates the EC2 instance, so the instance can only be named and tagged afterward with the modules currently used by this role.

Autobase's `Name` (EC2 instances) and `Cluster`/`cluster` values take precedence over conflicting custom values.
GCP requires label keys and values to use lowercase letters, numbers, underscores or hyphens. Keys must start with a lowercase letter.
The DigitalOcean cluster tag and GCP network tags remain unchanged because firewalls and load balancers use them to select servers.
Use strings for all keys and values (quote numeric values), and follow the selected provider's naming and count limits.
When backup storage uses a different provider, inherited tags must also satisfy that provider's restrictions.

| Provider | Resources tagged by this role | Exceptions |
|----------|-------------------------------|------------|
| AWS | SSH keys created by the role, security groups, EC2 instances, Spot requests, EBS volumes created with regular EC2 instances, CLB/NLB, NLB target groups, S3 buckets | ENIs are not tagged. EBS volumes attached to Spot instances may remain untagged. Existing VPCs/subnets and service-managed load balancer child resources are not modified. |
| GCP | VM instances and GCS buckets | System and data disks are not labeled. The Ansible modules used for global static load balancer IP addresses, forwarding rules, backend services, health checks, proxies, unmanaged instance groups and VPC firewall rules do not expose labels. Existing networks/subnets are not modified. |
| Azure | Resource groups, VNets created by the role, public IPs, security groups, NICs, VMs, load balancers and backup storage accounts | OS and data managed disks are not tagged. Subnets, load balancer child configurations and Blob containers do not support resource tags. Tags on a resource group are not inherited automatically. |
| DigitalOcean | Droplets | Data volumes cannot be tagged through the collection module. VPCs, SSH keys, firewalls, load balancers and Spaces buckets do not support resource tagging. Root disks and public IPs belong to the Droplet. |
| Hetzner Cloud | SSH keys created by the role, networks created by the role, firewalls, servers, volumes and load balancers | Primary IPs are not labeled. Subnetworks and load balancer services/targets are child configurations without labels. Root disks belong to the server. Object Storage bucket tagging is unsupported. |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
