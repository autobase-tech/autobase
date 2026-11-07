# Autobase Automation: Ansible Collection

This repository contains the `vitabaks.autobase` Ansible Collection — part of the Autobase project for automating the PostgreSQL cluster lifecycle.

**Autobase for PostgreSQL®** automates the deployment and management of highly available PostgreSQL clusters in production environments. This solution is tailored for use on dedicated physical servers, virtual machines, and within both on-premises and cloud-based infrastructures.

For a detailed overview of cluster components, see the [Architecture](https://autobase.tech/docs/overview/architecture) page.

## Using this collection

To install the latest version of the collection from [Ansible Galaxy](https://galaxy.ansible.com/vitabaks/autobase), use the following:

```bash
ansible-galaxy collection install vitabaks.autobase
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax where `X.Y.Z` can be any [available version](https://galaxy.ansible.com/ui/repo/published/vitabaks/autobase/):

```bash
ansible-galaxy collection install vitabaks.autobase:X.Y.Z
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
  - name: vitabaks.autobase
    version: 2.11.0
```

#### Use Autobase playbook

1. Prepare your inventory file

Note: It should follow the example [inventory](https://github.com/autobase-tech/autobase/blob/main/automation/inventory.example) structure and include required groups such as `master`, `replica` (as part of the `postgres_cluster` group), `etcd_cluster`, and others.

2. Prepare your variables file

Refer to the default [variables](https://github.com/autobase-tech/autobase/blob/main/automation/roles/common/defaults/main.yml) for all configurable options. You can override them via group_vars, host_vars, or directly in your inventory.

3. Run the Autobase playbook

Execute it directly:

```bash
ansible-playbook -i inventory vitabaks.autobase.deploy_pgcluster
```

Or include the playbook in your project by calling it from within an existing playbook:

```yaml
- name: Autobase
  hosts: all
  become: true
  become_user: root
  gather_facts: true
  any_errors_fatal: true

- name: Run Autobase playbook
  ansible.builtin.import_playbook: vitabaks.autobase.deploy_pgcluster
```

Tip: Start with `deploy_pgcluster` for initial provisioning, then use `config_pgcluster` for further configuration changes.

#### How to start from scratch

If you need to start from the very beginning, you can use the `remove_cluster` playbook.

Available variables:

- `remove_postgres`: stop the PostgreSQL service and remove data
- `remove_etcd`: stop the ETCD service and remove data
- `remove_consul`: stop the Consul service and remove data

⚠️ Caution: Only use this in non-production or when you’re absolutely sure.

## Internal Structure: Roles and Playbooks

Autobase adheres to a modular design separating atomic logic (roles) and orchestration logic (playbooks):

- **Roles** under `roles/` are designed to perform focused, reusable tasks (e.g., configuring Patroni, setting up firewall rules, installing extensions).  
  Most roles are not intended to be used standalone, but instead serve as building blocks.
- **Playbooks** under `playbooks/` implement orchestration logic — combining roles into coherent workflows such as deploying a cluster, upgrading PostgreSQL, or performing cleanup.  
  These playbooks represent full automation scenarios and manage host group coordination, conditions, and lifecycle sequencing.

## List of Playbooks

#### Infrastructure

- `cloud_resources` – Provision and configure cloud resources on AWS, GCP, Azure, DigitalOcean, and Hetzner Cloud. Note: also called by `deploy_pgcluster` when `cloud_provider` is defined.

#### Deployment

- `deploy_pgcluster` – Deploy a new highly available PostgreSQL cluster. This playbook also includes:
  - `etcd_cluster` – Provision and configure a new etcd cluster as the DCS (used if dcs_type: etcd).
  - `consul_cluster` – Provision and configure a new Consul cluster as the DCS (used if dcs_type: consul).
  - `balancers` – Deploy HAProxy for routing client traffic (used if with_haproxy_load_balancing: true).
  - `pgdog` – Deploy [PgDog](roles/pgdog/README.md) as a replacement for PgBouncer and HAProxy (used if pgdog_install: true). Optional and disabled by default; requires glibc 2.39+ (Debian 13, Ubuntu 24.04+, RHEL family 10).

#### Maintenance

- `config_pgcluster` – Reconfigure PostgreSQL cluster settings (users, databases, extensions, etc.) after the initial deployment.
- `stop_pgcluster` – Gracefully stop the entire Patroni cluster.
- `start_pgcluster` – Start the entire Patroni cluster.
- `restart_pgcluster` – Restart PostgreSQL in the entire cluster.
- `stop_pgnode` – Stop PostgreSQL on a specific Patroni node. Set the required `patroni_stop_node_name` to the Patroni node name.
- `start_pgnode` – Start PostgreSQL on a specific Patroni node. Set the required `patroni_start_node_name` to the Patroni node name.
- `restart_pgnode` – Restart PostgreSQL on a specific Patroni node. Set the required `patroni_restart_node_name` to the Patroni node name.
- `switchover_pgcluster` – Switch the Patroni leader role to a replica.
- `failover_pgcluster` – Promote the Patroni replica when there is no healthy Patroni leader.
- `reinit_pgcluster` – Rebuild a Patroni replica. Set the required `patroni_reinit_member_name` to the Patroni node name.
- `update_pgcluster` – Perform rolling updates of PostgreSQL or system packages with minimal downtime.
- `pg_upgrade` – Perform a major version in-place upgrade of PostgreSQL with minimal downtime.
  - `pg_upgrade_rollback` - Performs a rollback of a PostgreSQL upgrade (if possible).
- `pg_logical_upgrade` - Upgrades the target cluster and converting a physical replica into a logical replica.
  - `pg_logical_switchover` - Redirects PostgreSQL traffic from the source cluster to the target cluster with near-zero downtime.
  - `pg_logical_switchover_rollback` -  Switches PostgreSQL traffic back to the source cluster.
  - `pg_logical_replication_stop` - Clean up publications, subscriptions, and replication slots.
- `enable_backups` – Enable pgBackRest or WAL-G for an existing PostgreSQL cluster. If `cloud_backup_provider` is defined, the playbook can also provision S3 or other supported cloud backup storage.
- `backup_pgcluster` – Run the pgBackRest or WAL-G backup command on the current Patroni leader, or on the host set in `backup_pgcluster_target`.
- `backup_list` – Display the list of pgBackRest or WAL-G backups in text or JSON format.
- `restore_pgcluster` – Restore the current PostgreSQL cluster from a pgBackRest or WAL-G backup. Archiving is preserved by default; when cloning into an independent cluster, explicitly set `disable_archive_command: true` to prevent archiving to the source repository.

#### Scaling

- `add_node` – Add a new node to an existing cluster.

#### Removal

- `remove_node` – Remove a node from an existing cluster. Set the required `node_to_remove` to the node's `inventory_hostname` or `ansible_hostname`.
- `remove_cluster` – Remove the PostgreSQL cluster and, optionally, its DCS (etcd or Consul), including all data.
