# Ansible Role: selinux

Configures SELinux on RHEL-based hosts (RHEL, Rocky Linux, AlmaLinux, Oracle Linux, CentOS Stream).

## Description

- Sets the SELinux mode (`enforcing` or `permissive`) when `selinux_state` is set.
- Labels the PostgreSQL data, WAL and log directories (`postgresql_db_t`, `postgresql_log_t`), including
  custom locations such as `/pgdata` and their parent directories that have no file context of their own.
- With `selinux_confine_services: true`, builds and loads an `autobase_<service>` policy module for each
  service on the host. Patroni then runs in its own domain (`patroni_t`) and starts PostgreSQL in the
  distribution's `postgresql_t` domain. Without it, both run as `unconfined_service_t`, which SELinux does
  not restrict even in enforcing mode.
- Does nothing on hosts where SELinux is disabled or not available (Debian, Ubuntu).
- Never reboots. Enabling SELinux on a host where it is disabled requires a reboot and a relabel, which is left to the operator.

## Role Variables

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| selinux_state | "" | string | `enforcing`, `permissive`, or empty to leave the current mode unchanged. |
| selinux_policy | targeted | string | SELinux policy name. |
| selinux_confine_services | false | bool | Run the cluster services in their own SELinux domains (`autobase_*` policy modules). |
| selinux_policy_module_dir | /usr/share/selinux/autobase | path | Where the policy module sources are copied and built. |

## Notes

- Running processes keep their domain until Patroni is restarted. The role does not restart Patroni;
  on an existing cluster, restart one node at a time (replicas first).
- The policy module covers Patroni and PostgreSQL. etcd, Consul, PgBouncer and confd keep their current domains.
- The `SELinux (KVM)` workflow deploys a cluster on virtual machines with SELinux enabled and fails if Patroni or
  PostgreSQL runs unconfined, if a directory is mislabelled, or if any denial was logged.

## Tags

- `selinux`
- `selinux_contexts` (file contexts only)
- `selinux_policy` (policy module only)
