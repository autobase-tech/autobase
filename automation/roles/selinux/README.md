# Ansible Role: selinux

Configures SELinux on RHEL-based hosts (RHEL, Rocky Linux, AlmaLinux, Oracle Linux, CentOS Stream).

## Description

- Sets the SELinux mode (`enforcing` or `permissive`) when `selinux_state` is set.
- Labels the PostgreSQL data, WAL and log directories (`postgresql_db_t`, `postgresql_log_t`), including
  custom locations such as `/pgdata` and their parent directories that have no file context of their own.
- With `selinux_confine_services: true`, builds and loads an `autobase_<service>` policy module for each
  service on the host (see below). Without it, the services run as `unconfined_service_t` (or `initrc_t`),
  which SELinux does not restrict even in enforcing mode, and the haproxy and keepalived roles set
  `haproxy_t` and `keepalived_t` to permissive.
- Does nothing on hosts where SELinux is disabled or not available (Debian, Ubuntu).
- Never reboots. Enabling SELinux on a host where it is disabled requires a reboot and a relabel, which is left to the operator.

## Role Variables

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| selinux_state | "" | string | `enforcing`, `permissive`, or empty to leave the current mode unchanged. |
| selinux_policy | targeted | string | SELinux policy name. |
| selinux_confine_services | false | bool | Run the cluster services in their own SELinux domains (`autobase_*` policy modules). |
| selinux_policy_module_dir | /usr/share/selinux/autobase | path | Where the policy module sources are copied and built. |

## Domains

| Service | Domain | Module | Installed when |
|---------|--------|--------|----------------|
| Patroni | `patroni_t` | `autobase_patroni` | host in `postgres_cluster` |
| PostgreSQL | `postgresql_t` (base policy) | `autobase_patroni` | host in `postgres_cluster` |
| pgBackRest | `pgbackrest_t` | `autobase_pgbackrest` | `pgbackrest_install` |
| WAL-G | `walg_t` | `autobase_walg` | `wal_g_install` |
| PgBouncer | `pgbouncer_t` | `autobase_pgbouncer` | `pgbouncer_install` |
| etcd | `etcd_t` | `autobase_etcd` | host in `etcd_cluster`, `dcs_type: etcd` |
| Consul | `consul_t` | `autobase_consul` | host in `consul_instances`, `dcs_type: consul` |
| HAProxy | `haproxy_t` (base policy, enforcing) | `autobase_haproxy` | `with_haproxy_load_balancing` |
| confd | `confd_t` | `autobase_confd` | `with_haproxy_load_balancing`, `confd_install` |
| keepalived | `keepalived_t` (base policy, enforcing) | `autobase_keepalived` | HAProxy with `cluster_vip` |
| vip-manager | `vip_manager_t` | `autobase_vip_manager` | `cluster_vip` without HAProxy |

pgBackRest and WAL-G change into their domain when PostgreSQL runs them as `archive_command`/`restore_command`,
when Patroni runs them to create a replica, and when systemd or cron start them. The role also assigns port types
for etcd (2379-2380), PgBouncer (`pgbouncer_listen_port`) and Consul (8300-8302, 8400, 8500, 8502-8503, 8600).

## Notes

- Running processes keep their domain until they restart. The role restarts nothing; on an existing cluster,
  restart the services one node at a time (replicas first for Patroni).
- Policy modules are compiled on the host (`selinux-policy-devel`) and rebuilt only when their source changes.
- Service roles call `tasks_from: relabel` with the paths they install or create, so files that existed before
  the modules were loaded get their labels before the service starts.
- Not covered: pg_probackup, netdata, a dedicated pgBackRest repository host, and the Consul DNS forwarding
  (dnsmasq/systemd-resolved).
- The `SELinux (KVM)` workflow deploys clusters on virtual machines with SELinux enabled (etcd with HAProxy,
  keepalived and pgBackRest; Consul with vip-manager and WAL-G) and fails if a service runs outside its domain,
  if a file is mislabelled, if a service does not work, or if any denial was logged for the service domains.

## Tags

- `selinux`
- `selinux_contexts` (file contexts only)
- `selinux_policy` (policy module only)
