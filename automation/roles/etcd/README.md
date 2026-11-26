# Ansible Role: etcd

This role installs and configures [etcd](https://etcd.io/), a distributed, reliable key-value store used as the backend for service discovery and cluster coordination, serving as the Distributed Configuration Store (DCS) for Patroni.

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `etcd_version` | `3.6.13` | etcd version. |
| `etcd_cluster_name` | `"etcd-{{ cluster_name }}"` | etcd cluster name (token). |
| `etcd_bind_address` | `""` | IP address to bind etcd services (tasks fall back to `bind_address` when unset). |
| `etcd_conf_dir` | `/etc/etcd` | etcd configuration directory. |
| `etcd_data_dir` | `/var/lib/etcd` | etcd data directory. |
| `etcd_tls_enable` | `true` | Enables TLS encryption with a self-signed certificate if 'tls_cert_generate' is true. |
| `etcd_tls_dir` | `"{{ etcd_conf_dir }}/tls"` | TLS directory on hosts. |
| `etcd_tls_ca_crt` | `ca.crt` | CA filename |
| `etcd_tls_ca_key` | `ca.key` | CA key filename |
| `etcd_tls_server_crt` | `server.crt` | Server certificate filename |
| `etcd_tls_server_key` | `server.key` | Server key filename |
| `etcd_client_cert_auth` | `true` if not etcd_on_dedicated_nodes else `false` | Enable etcd client certificate authentication.  |
| `patroni_etcd_protocol` | `https` if etcd_tls_enable else `http` | Scheme for etcd endpoints used by etcdctl. |
| `etcd_package_repo` | `"https://github.com/etcd-io/etcd/releases/download/v{{ etcd_version }}/etcd-v{{ etcd_version }}-linux-{{ etcd_architecture_map[ansible_architecture] }}.tar.gz"` | Binary URL for installation. |
| `etcd_installation_method` | `binary` | Install method. When set to `"{{ pkg_type }}"`, system package manager is used and `etcd_package_repo` is ignored. |
| `etcd_bin_dir` | `/usr/bin` if etcd_installation_method == pkg_type else `/usr/local/bin` }}` | Installation directory for etcd. |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
