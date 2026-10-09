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

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
