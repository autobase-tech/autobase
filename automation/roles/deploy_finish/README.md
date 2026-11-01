# Ansible Role: deploy_finish

Auxiliary role that prints PostgreSQL cluster information and connection details at the end of a playbook run.

## What it prints
- PostgreSQL users list
- PostgreSQL databases list
- Patroni cluster status (patronictl list)
- Connection endpoints depending on environment:
  - etcd + cluster_vip (with/without HAProxy)
  - etcd without VIP (HAProxy or direct PostgreSQL, with optional PgBouncer)
  - Consul-based DNS names
  - Cloud load balancers (AWS NLB, GCP, Azure, DigitalOcean, Hetzner)

For clusters without a VIP or load balancer, connection details include multi-host libpq URIs named `primary` and `replica`, with [`target_session_attrs=primary` and `standby`](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-TARGET-SESSION-ATTRS), using the PgBouncer port when installed or the PostgreSQL port otherwise. PgBouncer connects to the local PostgreSQL instance on each node, so libpq can select a node with the required role through it. These URIs require libpq 14 or newer; `load_balance_hosts=random`, included for configured PostgreSQL versions 16 and newer, requires libpq 16 or newer.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
