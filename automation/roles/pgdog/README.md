# Ansible Role: pgdog

This role installs PgDog to pool connections, balance queries, and route them across PostgreSQL shards. [PgDog project](https://github.com/pgdogdev/pgdog)

> [!IMPORTANT]
> PgDog is licensed under AGPL-3.0. Autobase installs the upstream binary as a separate program. Review your organization's policy on AGPL software before enabling this role. [PgDog license](https://github.com/pgdogdev/pgdog/blob/main/LICENSE)

## Requirements

- **PostgreSQL 12 or newer** for automatic role detection and replication lag monitoring.
- **glibc 2.39 or newer** to run the upstream binaries. Supported platforms include Ubuntu 24.04+, Debian 13+, and RHEL 10 and its derivatives.
- `x86_64` or `aarch64` servers.

## How it works

PgDog runs alongside PostgreSQL on every node of the `postgres_cluster` group. Each instance knows about all the nodes, so clients can connect to any of them directly or through a load balancer.

- PgDog sends writes to the primary of the relevant shard, regardless of which PgDog instance the client uses.
- A shard's primary and replicas can serve reads according to `pgdog_read_write_split`.
- PgDog checks each PostgreSQL node's role and replication lag every `pgdog_lsn_check_interval` milliseconds. Patroni promotes replicas, and PgDog detects the resulting role changes.

## Usage

```yaml
pgdog_install: true
```

Enabling PgDog sets the default for `pgbouncer_install` to `false`. Set it to `false` if you previously enabled it explicitly. Leave `with_haproxy_load_balancing` disabled and `cluster_vip` empty.

## Deploy a sharded cluster

The example defines four independent Patroni clusters that share a PgDog routing configuration. Set `cluster_name` for the logical cluster and assign each PostgreSQL host an integer `shard_id`. Use consecutive IDs starting at `0`. Put one bootstrap member per shard in `master` and that shard's standbys in `replica`. [YAML inventory example](../../inventory.example.yml)

The logical name `orders-db` produces the Patroni scopes `orders-db-shard0` through `orders-db-shard3`. The cloud load balancer and Consul service use the logical name. Shards can share an etcd or Consul quorum.

Declare databases in `postgresql_databases` and create the application tables on each shard. Replace the example password for `orders_user` in `postgresql_users` before deployment. Use the same credentials on all shards.

Define routing in `pgdog_sharded_tables`. The `database` field names the PgDog pool. The rules below route a user and their orders to the same shard when `orders.user_id` matches `users.id`.

```yaml
pgdog_sharded_tables:
  - database: orders
    name: users
    column: id
    data_type: bigint
  - database: orders
    name: orders
    column: user_id
    data_type: bigint
```

Use the same sharding key types on each shard. Coordinate sequences if IDs must be globally unique. PgDog may route a query to multiple shards when it cannot identify the relevant sharding key. [PgDog sharded tables](https://docs.pgdog.dev/configuration/pgdog.toml/sharded_tables/) · [Supported SQL](https://docs.pgdog.dev/features/sharding/supported-queries/)

The shard set is fixed at deployment. Autobase checks the stored cluster name, local shard ID, and full shard set when deploying or publishing configuration. To change the number of shards, provision a separate target cluster and redistribute the data. [PgDog discussion on adding shards](https://github.com/pgdogdev/pgdog/issues/828)

Deploy all shards together using the complete inventory.

```bash
ansible-playbook -i inventory.yml vitabaks.autobase.deploy_pgcluster
```

### Cloud server placement

This example provisions four shards with three VMs each.

```yaml
cluster_name: orders-db
pgdog_install: true
shards_count: 4
servers_per_shard: 3
```

Each shard has one bootstrap VM (`pg01`) and two replicas (`pg02` and `pg03`). VM names include the shard ID, for example `orders-db-shard0-pg01`.

For examples of adding replicas across all shards or placing one replica in a specific shard, see [Shard placement in cloud_resources](../cloud_resources/README.md#shard-placement).

### Shard maintenance

Pass the complete inventory to maintenance playbooks and set `target_shard` to select a shard. The default is `all`. Use `target_shard=all` when changing shared users, passwords, or database definitions.

```bash
ansible-playbook -i inventory.yml vitabaks.autobase.switchover_pgcluster -e target_shard=1
ansible-playbook -i inventory.yml vitabaks.autobase.backup_pgcluster -e target_shard=1
ansible-playbook -i inventory.yml vitabaks.autobase.backup_list -e target_shard=1
```

To add a replica, assign it an existing shard ID, set `new_node: true`, run `add_node.yml`, then clear the flag. The playbook adds the backend to each PgDog instance.

### Backup and restore

pgBackRest uses one stanza per shard. Use a shared or dedicated repository to make each shard's backups available after a switchover. WAL-G appends the shard's Patroni scope to each configured storage prefix. To recover one shard, run `restore_pgcluster.yml -e target_shard=1` with that shard's backup settings.

For an application-consistent recovery point, stop writers and drain in-flight transactions across all shards. Record a recovery point on each primary and verify that the WAL containing each recovery point has been archived before resuming writes. During recovery, keep traffic paused until each shard reaches its recorded point.

## Client entry point

Clients use `pgdog_listen_port` (`6432` by default) for both reads and writes. To distribute connections across PgDog instances, use a TCP load balancer or balance new connections in the client.

- **TCP load balancer.** Use a single address for clients, add every PgDog instance as a backend, and run TCP health checks on `pgdog_listen_port`. Autobase uses this setup when provisioning a cloud load balancer.
- **Client-side balancing.** Try PgDog hosts in a random order for each new connection and move on to the next host if a connection is refused or times out. With libpq 16 or later, pass a list of PgDog hosts and set `load_balance_hosts=random` with a finite `connect_timeout`. Keep `target_session_attrs` at its default, `any`, to accept a successful connection to any PgDog instance. [libpq connection parameters](https://www.postgresql.org/docs/16/libpq-connect.html#LIBPQ-CONNECT-LOAD-BALANCE-HOSTS)

This `psql` command passes the addresses of all eight PgDog nodes from the example inventory as one connection string. [psql reference](https://www.postgresql.org/docs/16/app-psql.html)

```bash
psql 'host=10.128.64.140,10.128.64.141,10.128.64.142,10.128.64.143,10.128.64.144,10.128.64.145,10.128.64.146,10.128.64.147
port=6432 dbname=orders user=orders_user load_balance_hosts=random connect_timeout=3'
```

Clients must reconnect after losing an established connection.

### Cloud load balancer

When provisioning cloud resources with `cloud_load_balancer: true`, Autobase creates one endpoint for all PgDog instances. It uses `cluster_name` for the endpoint and checks PgDog directly over TCP. Connection info shows the shared address and port. When switching an existing cluster to PgDog, retire the former role-specific load balancers after moving clients to the PgDog endpoint.

PgDog must listen on `0.0.0.0` (the default) to accept traffic addressed to this IP.

### Consul service discovery

With `dcs_type: consul`, Autobase registers each PgDog instance under `cluster_name` with a `pgdog` tag and a TCP health check on `pgdog_listen_port`. For `orders-db` and the default Consul domain, use `pgdog.orders-db.service.consul` and the configured PgDog port. Clients need Consul DNS resolution through a local agent or DNS forwarding. [Consul DNS lookups](https://developer.hashicorp.com/consul/docs/discover/service/static)

PgDog registrations replace Patroni's role-based service registration. Autobase removes service definition files outside `consul_services` and `consul_cleanup_ignore_files` and restarts Consul when definitions change. Existing clusters can apply the change with `config_pgcluster.yml --tags patroni_conf,pgdog`.

## Switch an existing cluster to PgDog

Set `pgdog_install: true`, clear `cluster_vip`, and set `pgbouncer_install: false` and `with_haproxy_load_balancing: false` if they were enabled. Prepare the replacement client endpoint and stop the former HAProxy or VIP services separately if they are in use.

Run `config_pgcluster.yml -e pgbouncer_disable=true` during a maintenance window. Autobase prepares the PgDog configuration, stops and disables the detected PgBouncer services, then starts PgDog. Clients using PgBouncer must reconnect to PgDog. With the default TLS settings, use a TLS-capable client.

To move an existing unsharded workload to multiple shards, deploy a separate sharded cluster and migrate the data.

## Differences from PgBouncer and HAProxy

| Topic | PgBouncer and HAProxy | PgDog |
|-------|-----------------------|-------|
| Read/write routing | One port per role, chosen by the client | One port. PgDog parses queries to select a backend. Use `SET pgdog.role TO 'primary'` before a `SELECT` that calls a function that writes |
| Read consistency | Clients select a primary or replica endpoint | Reads can use lagging replicas. Set `pgdog_read_write_split: "prefer_primary"` to route reads to the primary by default |
| Default pooling mode | `session` | `transaction` |
| Replica selection | Patroni REST API, including `balancer_tags`, the sync/async roles and `patroni_maximum_lag_on_replica` | PgDog detects roles with `pg_is_in_recovery()` and excludes replicas that exceed `pgdog_ban_replica_lag_bytes` (100 MiB by default) |
| Authentication | `auth_query` | Passthrough by default. PgDog validates client passwords against PostgreSQL |
| Client passwords | MD5 or SCRAM exchange by default | Passthrough uses cleartext password authentication inside TLS by default |
| Databases | The `*` wildcard serves all of them | Only the configured ones. Run `config_pgcluster.yml` with the tag `pgdog_conf` after creating a database |
| Pool size | Local to each node | Each instance connects to the primary, so count `pool_size * <number of nodes>`, per database and per user. The pre-checks compare the lowest possible total with `max_connections` |
| In-place major upgrade | `PAUSE` | `MAINTENANCE ON` holds the client queries and lets the running transactions finish |
| Blue-green upgrade | Autobase can redirect traffic through PgBouncer | Switch client traffic manually. Follow the [upgrade instructions](../upgrade/README.md) |
| Monitoring | Netdata collector, `pgbouncer_exporter` | Built-in OpenMetrics endpoint on `pgdog_openmetrics_port`, enabled by `prometheus_exporters_install` |

## Role Variables

The variables are defined in [`roles/common/defaults/main.yml`](../common/defaults/main.yml).

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `pgdog_install` | `false` | Enable or disable PgDog installation and configuration |
| `pgdog_version` | see defaults | The PgDog version to install |
| `pgdog_package_repo` | GitHub release | URL of the release archive. Point it to a mirror for offline installations |
| `pgdog_package_checksum` | `sha256:<url>.sha256` | Checksum of the archive, or `""` to skip the verification |
| `pgdog_conf_dir` | `"/etc/pgdog"` | Configuration directory |
| `pgdog_listen_addr` | `"0.0.0.0"` | IP address for PgDog to bind to |
| `pgdog_listen_port` | `6432` | Port for PgDog to listen on |
| `pgdog_workers` | `vCPUs * 2` | Number of threads |
| `pgdog_general_parameters` | `{}` | Any other option of the [`[general]`](https://docs.pgdog.dev/configuration/pgdog.toml/general/) section |

### Pooling and load balancing

| Variable | Default | Description |
|----------|---------|-------------|
| `pgdog_default_pool_size` | `20` | Maximum server connections per pool, node and PgDog instance |
| `pgdog_min_pool_size` | `1` | Minimum server connections per pool |
| `pgdog_pooler_mode` | `"transaction"` | `transaction`, `session` or `statement`. Reads are not split in `session` mode |
| `pgdog_read_write_split` | `"include_primary"` | `include_primary`, `exclude_primary`, `include_primary_if_replica_banned` or `prefer_primary` |
| `pgdog_read_write_strategy` | `"conservative"` | `conservative` or `aggressive` |
| `pgdog_load_balancing_strategy` | `"random"` | `random`, `round_robin` or `least_active_connections` |
| `pgdog_lsn_check_interval` | `1000` | How often to check the role and lag of the nodes, in milliseconds |
| `pgdog_ban_replica_lag_bytes` | `104857600` (100 MiB) | Replication lag threshold in bytes for excluding replicas from reads. Use `""` to disable this threshold |
| `pgdog_ban_timeout` | `30000` | Ban timeout in milliseconds. PgDog continues monitoring the backend while it is banned |
| `pgdog_checkout_timeout` | `5000` | Maximum wait for a backend connection, in milliseconds. Failover duration also depends on role detection and retries |
| `pgdog_shutdown_timeout` | `60000` | How long to wait for active transactions on shutdown, in milliseconds |
| `pgdog_prepared_statements_limit` | `5000` | Maximum prepared statements per server connection |
| `pgdog_healthcheck_port` | `""` | Port for the HTTP health check, for external load balancers |
| `pgdog_openmetrics_port` | `9090` with `prometheus_exporters_install`, otherwise `""` | Port for the OpenMetrics (Prometheus) endpoint, or `""` to disable it |
| `pgdog_openmetrics_namespace` | `"pgdog_"` | Prefix of the metric names of the OpenMetrics endpoint (PgDog has none by default), or `""`. Ignored if `openmetrics_namespace` is set in `pgdog_general_parameters` |

### Databases and users

| Variable | Default | Description |
|----------|---------|-------------|
| `pgdog_pools` | One pool for `postgres` | Add or customize pools. Autobase adds entries from `postgresql_databases` unless a pool with that name is already defined |
| `pgdog_sharded_tables` | `[]` | Routing rules by PgDog pool, table, sharding column, and key type. The optional `schema` qualifies the table |
| `pgdog_users` | `[]` | The entries of [`users.toml`](https://docs.pgdog.dev/configuration/users.toml/users/). Only required with `pgdog_passthrough_auth: "disabled"`, or to customize the pool of a user |
| `pgdog_passthrough_auth` | `enabled_allow_change` with TLS, `enabled_plain_allow_change` without | The [passthrough authentication](https://docs.pgdog.dev/features/auth/password/#passthrough-authentication) mode, or `disabled` |
| `pgdog_auth_type` | `md5` for PostgreSQL MD5 authentication, otherwise `scram` | Authentication method for `pgdog_users` |
| `pgdog_admin_username` | `"admin"` | User of the `admin` database |
| `pgdog_admin_password` | generated | Password of the `admin` database |

```yaml
pgdog_pools:
  - { name: "postgres", dbname: "postgres", pool_parameters: {} }
  - { name: "reports", dbname: "mydatabase", pool_parameters: { pool_size: 10, pooler_mode: "session" } }
```

`pool_parameters` is a dictionary of database options. In sharded deployments, set shard membership and backend addresses in the inventory. [PgDog database settings](https://docs.pgdog.dev/configuration/pgdog.toml/databases/)

With an `allow_change` mode, PgDog can update a pool's cached credentials after a client authenticates with the new PostgreSQL password. Until PgDog updates its cache, it may still accept the old password. The other passthrough modes use a static password for each pool.

With `allow_change`, one client login attempt with an invalid password can result in several failed logins in PostgreSQL. Use these modes with trusted clients. [PgDog password authentication](https://docs.pgdog.dev/features/auth/password/#changing-passwords)

### TLS

| Variable | Default | Description |
|----------|---------|-------------|
| `pgdog_client_tls_required` | `tls_cert_generate` | Reject the clients that do not use TLS |
| `pgdog_tls_verify` | `verify_ca` with `tls_cert_generate`, otherwise `prefer` | How to verify the certificates of the PostgreSQL servers |
| `pgdog_tls_dir` | `tls_dir` | Directory of the certificates |
| `pgdog_tls_cert_file` | `tls_cert` | Certificate file |
| `pgdog_tls_key_file` | `tls_privatekey` | Private key file |
| `pgdog_tls_ca_file` | `tls_ca_cert` | CA certificate file |

## Operations

Autobase writes `users.toml` first, then runs `pgdog configcheck` before replacing `pgdog.toml`. Both files are in `pgdog_conf_dir`. The `pgdog` service logs to the systemd journal.

PgDog can reload most configuration changes while keeping client connections open. Restart the service after changing `pgdog_listen_addr`, `pgdog_listen_port`, `pgdog_workers`, `pgdog_openmetrics_port`, or `pgdog_openmetrics_namespace`.

After a failover, some replicas can be left out of the load balancer until PgDog has checked them and their bans have expired. Bans normally expire after `pgdog_ban_timeout` (30 seconds); an unhealthy or lagging replica can remain excluded longer. Reads go to the other eligible nodes in the meantime. If all targets are unavailable, PgDog can clear bans earlier to retry them.

The `add_node.yml` and `remove_node.yml` playbooks update the backend list across the cluster. Run `config_pgcluster.yml --tags pgdog_conf` to refresh PgDog configuration after changing databases or routing rules.

To upgrade PgDog, set `pgdog_version` and run `update_pgcluster.yml -e target=pgdog`. The playbook updates replicas one at a time, then updates the primaries. PgDog restarts after a binary change, with one restart at a time. A failed readiness check stops the playbook. `target=system` also updates PgDog. Use the update playbook for version changes because `config_pgcluster.yml --tags pgdog` can install binaries across the cluster in the same play.

A restart waits for running transactions to finish, for up to `pgdog_shutdown_timeout`, and fails if PgDog does not accept connections within 60 seconds. Clients connected to the restarted node have to reconnect.

Connect to the admin database to inspect a running instance.

```bash
psql -h 127.0.0.1 -p 6432 -U admin -d admin -c "SHOW REPLICATION" -c "SHOW POOLS"
```

## Tags

- `pgdog`: all tasks
- `pgdog_install`: install the release
- `pgdog_service`: configure the systemd service
- `pgdog_conf`: update the configuration files
