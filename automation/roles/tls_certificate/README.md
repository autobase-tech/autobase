# Ansible Role: tls_certificate

Generates and manages TLS certificates for the cluster. Creates a self-signed CA and server certificate/key (with SANs), and distributes them to all nodes.

### How it works
- Generation (tasks/main.yml):
  - Creates CA (ca.crt/ca.key) and server cert/key (server.crt/server.key) under tls_dir.
  - SANs are auto-built from hostnames/FQDNs/IPs of hosts in tls_group_name unless tls_subject_alt_name variable is provided.
  - Skips if files exist; override with tls_cert_regenerate/tls_ca_regenerate.
- Distribution (tasks/copy.yml):
  - Reads files from tls_source_host (or the first host in tls_group_name by default) and copies them to all nodes.
  - When available, the CA private key is copied as root:root with mode 0400; other files use the configured TLS owner.

## Main Role Variables

| Variable | Default | Description |
|---|---|---|
| tls_cert_generate | true | Generate a self-signed certificate.. |
| tls_cert_regenerate | false | Force server cert/key regeneration. |
| tls_ca_regenerate | false | Force CA regeneration. |
| tls_cert_valid_days | 3650 | Default validity (days) for self-signed certs. |
| tls_dir | /etc/tls | Base directory for TLS assets. |
| tls_cert | server.crt | Server certificate filename. |
| tls_privatekey | server.key | Server private key filename. |
| tls_ca_cert | ca.crt | CA certificate filename. |
| tls_ca_key | ca.key | CA private key filename. |

## Additional Variables
| Variable | Default | Description |
|---|---|---|
| tls_group_name | postgres_cluster | Inventory group to derive SANs from and to pick the “first” host. |
| tls_source_host | first host in tls_group_name | Host that owns the CA private key and generates/distributes certificates. |
| tls_subject_alt_name | "" | Comma-separated SANs; if empty, auto-generated from ansible_hostname, ansible_fqdn, and bind addresses. |
| tls_owner | postgres | Default owner used when copying certs/keys to nodes. |
| generate_tls_dir | unset -> tls_dir | Override generation directory. |
| generate_tls_cert | unset -> tls_cert | Override server cert filename. |
| generate_tls_privatekey | unset -> tls_privatekey | Override server key filename. |
| generate_tls_ca_cert | unset -> tls_ca_cert | Override CA cert filename. |
| generate_tls_ca_key | unset -> tls_ca_key | Override CA key filename. |
| generate_tls_common_name | unset -> tls_common_name -> cluster_name | CN for server cert. |
| generate_tls_ca_common_name | Autobase CA | CN for CA. |
| generate_tls_privatekey_size | 4096 | Key size for generated keys. |
| generate_tls_privatekey_type | RSA | Key type (e.g., RSA). |
| generate_tls_cert_provider | selfsigned | Provider for CA (x509 self-signed). |
| generate_tls_cert_valid_days | unset -> tls_cert_valid_days | Validity (days) for server cert. |
| generate_tls_group | root | Group owner for the generated server certificate file. |
| fetch_tls_dir | tls_dir | Source dir on the delegate host for copy step. |
| fetch_tls_privatekey | tls_privatekey | Source key filename for copy step. |
| fetch_tls_cert | tls_cert | Source cert filename for copy step. |
| fetch_tls_ca_cert | tls_ca_cert | Source CA filename for copy step. |
| copy_tls_dir | tls_dir | Destination dir on all nodes when copying. |
| copy_tls_owner | tls_owner | Owner for copied files (key mode 0400, cert/CA 0644). |
| copy_tls_privatekey | tls_privatekey | Destination key filename. |
| copy_tls_cert | tls_cert | Destination cert filename. |
| copy_tls_ca_cert | tls_ca_cert | Destination CA filename. |

Notes:
- SAN auto-detection uses one of: etcd_bind_address, consul_bind_address, patroni_bind_address, or bind_address, depending on tls_group_name.
- Generation and distribution use tls_source_host when provided; otherwise they use groups[tls_group_name][0] (default group “master” in copy.yml if tls_group_name is unset).
- Existing CA certificates are preserved when only the server certificate is regenerated. Only tls_ca_regenerate may replace a CA.
- Cluster scaling requires both the existing CA certificate and its private key; the role stops instead of generating a replacement CA when either file is missing.
- When present on the source node, the CA private key is distributed to all target nodes by default, allowing any remaining node to become the certificate source after a host failure. Existing installations without the key continue copying the other TLS files.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
