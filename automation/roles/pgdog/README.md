# Ansible Role: pgdog

This role installs and configures [PgDog](https://github.com/pgdogdev/pgdog), a connection pooler, load balancer and database sharder for PostgreSQL.

> [!IMPORTANT]
> PgDog is licensed under [AGPL-3.0](https://github.com/pgdogdev/pgdog/blob/main/LICENSE), unlike the other components installed by Autobase. It is installed as a separate, unmodified program. If your organization has a policy on AGPL software, review it before you enable this role.

## How it works

PgDog runs on every node of the `postgres_cluster` group, next to PostgreSQL. Each instance knows about all the nodes, so clients can connect to any of them, for example through a VIP or a cloud load balancer:

- Writes are sent to the primary, whichever node the client is connected to.
- Reads are balanced between the replicas and the primary (see `pgdog_read_write_split`).
- PgDog checks `pg_is_in_recovery()` on every node each `pgdog_lsn_check_interval` milliseconds, and follows the failovers and switchovers performed by Patroni. PgDog never promotes a replica by itself.

## Client entry point

PgDog replaces the routing that HAProxy does, not a stable address for clients. It runs on the database nodes, so if a node goes down, clients connected to its PgDog lose that connection and need another way in. Use Consul service discovery, `cluster_vip` (handled by vip-manager, which follows the Patroni leader), a cloud load balancer, or a libpq multi-host connection string.

There is also a single port, because PgDog routes each query. With `cloud_load_balancer: true`, Autobase configures one shared load balancer targeting every PgDog instance, named after `patroni_cluster_name` without a role suffix. The replica, sync and async load balancer flags are ignored. Health checks use TCP on `pgdog_listen_port`, independently of the role or health of the local Patroni instance. Connection info shows one `address` and port. Switching an existing cluster to PgDog creates a new endpoint; previously created load balancers are not automatically deleted.

On GCP, `database_public_access: false` creates a regional internal passthrough Network Load Balancer with a static private IP from the selected subnetwork. PgDog must listen on `0.0.0.0` (the default) to accept traffic addressed to this IP. Clients in other VPC regions can also use the endpoint, subject to routing and firewall rules. With `database_public_access: true`, GCP uses an external TCP proxy load balancer.

With `pgdog_install: true` and `dcs_type: consul`, Consul serves as the DCS for Patroni and discovers the PgDog instances. Autobase registers each instance under the cluster service name with the `pgdog` tag and a TCP health check on `pgdog_listen_port`. Clients use one address, for example `pgdog.postgres-cluster-01.service.consul`, and port `6432` (or the configured `pgdog_listen_port`). Connection info shows this address without role-specific endpoints or `target_session_attrs`. The usual Consul datacenter syntax also applies, for example `pgdog.postgres-cluster-01.service.consul`.

Patroni service registration is disabled. The shared Consul service management tasks register the selected `consul_services` and remove undeclared service definition files, except those in `consul_cleanup_ignore_files`. Changes notify the Consul restart handler. Existing clusters can apply the change with `config_pgcluster.yml --tags patroni_conf,pgdog`. Clients need Consul DNS resolution through a local agent or DNS forwarding and must reconnect after a lost connection; DNS discovery does not preserve existing connections.

## Requirements

- **PostgreSQL 12 or newer**, required by the replication monitoring query used for automatic role detection.
- **glibc 2.39 or newer**, required by the binaries that PgDog publishes. That means Ubuntu 24.04+, Debian 13+, or RHEL 10 and its derivatives. It rules out Ubuntu 22.04, Debian 11 and 12, and RHEL 8 and 9. The pre-checks stop the deployment on these systems.
- `x86_64` or `aarch64` servers.

## Usage

```yaml
pgdog_install: true
```

`pgbouncer_install` defaults to `false` when PgDog is enabled, so it does not need to be set separately. Explicitly enabling PgBouncer or HAProxy together with PgDog is rejected by the pre-checks. With `pgdog_install: false`, PgBouncer defaults to enabled, and it can be used together with HAProxy.

PgDog listens on port `6432`, like PgBouncer, so the connection info and the firewall rules stay the same. To switch an existing cluster, stop and disable the `pgbouncer` and `haproxy` services first, where installed, and then run `config_pgcluster.yml` with the tags `patroni_conf,pgdog`. Selecting PgDog does not stop or uninstall existing services. Keep in mind that clients will have to use TLS (see below).

## Differences from PgBouncer and HAProxy

| Topic | PgBouncer and HAProxy | PgDog |
|-------|-----------------------|-------|
| Read/write routing | One port per role, chosen by the client | One port. PgDog parses the queries. A `SELECT` that calls a function which writes is sent to a replica and fails. Use a transaction, or the `pgdog.role` parameter, for such queries |
| Read consistency | Reads go to the primary unless the client asks for a replica | Reads can be sent to replicas, and they may be behind the primary. Use `pgdog_read_write_split: "prefer_primary"` to change that |
| Default pooling mode | `session` | `transaction` |
| Replica selection | Patroni REST API, including `balancer_tags`, the sync/async roles and `patroni_maximum_lag_on_replica` | `pg_is_in_recovery()`. Replicas that lag behind by more than `pgdog_ban_replica_lag_bytes` (100MB) stop receiving reads. `balancer_tags` and the `/sync` and `/async` checks are not used |
| Authentication | `auth_query` | Passthrough: the password is checked against PostgreSQL on first use and when it changes |
| Client passwords | Never sent in clear text | Sent to PgDog in clear text, so clients have to use TLS (`pgdog_client_tls_required`) |
| Databases | The `*` wildcard serves all of them | Only the configured ones. Run `config_pgcluster.yml` with the tag `pgdog_conf` after creating a database |
| Pool size | Local to each node | Each instance connects to the primary, so count `pool_size * <number of nodes>`, per database and per user. The pre-checks compare the lowest possible total with `max_connections` |
| In-place major upgrade | `PAUSE` | `MAINTENANCE ON` holds the client queries and lets the running transactions finish |
| Blue-green upgrade | Traffic redirected automatically | Not supported yet, follow the [manual steps](../upgrade/README.md) |
| Monitoring | Netdata collector | Not configured. Set `pgdog_openmetrics_port` to expose the metrics in the OpenMetrics format |

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
| `pgdog_load_balancing_strategy` | `"random"` | `random`, `round_robin` or `least_active_connections`. With the latter, a lightly loaded cluster sends most reads to the primary, because ties go to the first node |
| `pgdog_lsn_check_interval` | `1000` | How often to check the role and lag of the nodes, in milliseconds |
| `pgdog_ban_replica_lag_bytes` | `104857600` (100MB) | Stop reading from replicas that lag behind by this amount of bytes, or `""` to disable. Replicas without valid lag measurements can also be excluded until measurements are available and their ban expires |
| `pgdog_ban_timeout` | `30000` | Ban expiry timeout in milliseconds; upstream uses 5 minutes. Monitoring continues during the ban. Expiry clears the ban only when the target is healthy and its lag is below the configured thresholds |
| `pgdog_checkout_timeout` | `5000` | Maximum wait for a server connection, in milliseconds. This is not a guaranteed failover duration: recovery also depends on role detection, connection errors and application retries |
| `pgdog_shutdown_timeout` | `60000` | How long to wait for active transactions on shutdown, in milliseconds |
| `pgdog_prepared_statements_limit` | `5000` | Maximum prepared statements per server connection |
| `pgdog_healthcheck_port` | `""` | Port for the HTTP health check, for external load balancers |
| `pgdog_openmetrics_port` | `""` | Port for the OpenMetrics endpoint |

### Databases and users

| Variable | Default | Description |
|----------|---------|-------------|
| `pgdog_pools` | `postgres` | The databases to serve, in addition to all the `postgresql_databases` |
| `pgdog_users` | `[]` | The entries of [`users.toml`](https://docs.pgdog.dev/configuration/users.toml/users/). Only required with `pgdog_passthrough_auth: "disabled"`, or to customize the pool of a user |
| `pgdog_passthrough_auth` | `enabled_allow_change` with TLS, `enabled_plain_allow_change` without | The [passthrough authentication](https://docs.pgdog.dev/features/auth/password/#passthrough-authentication) mode, or `disabled` |
| `pgdog_auth_type` | from `postgresql_password_encryption_algorithm` | Authentication of `pgdog_users` |
| `pgdog_admin_username` | `"admin"` | User of the `admin` database |
| `pgdog_admin_password` | generated | Password of the `admin` database |

```yaml
pgdog_pools:
  - { name: "postgres", dbname: "postgres", pool_parameters: {} }
  - { name: "reports", dbname: "mydatabase", pool_parameters: { pool_size: 10, pooler_mode: "session" } }
```

`pool_parameters` accepts the options of the [`[[databases]]`](https://docs.pgdog.dev/configuration/pgdog.toml/databases/) section. Unlike in `pgbouncer_pools`, it is a dictionary and not a string.

Passwords changed in PostgreSQL are picked up when a client logs in with the new password, and a wrong password is rejected without affecting the pool. The old password keeps working until then. Avoid the modes without `allow_change`: with them, PgDog rejects the new password and keeps accepting the old one until it is restarted.

With `allow_change`, each wrong password is checked against PostgreSQL. PgDog retries on all nodes for `pgdog_checkout_timeout` before it rejects the client, which is 51 failed logins in the PostgreSQL logs of a 3-node cluster with the default timeout. Take that into account if you monitor failed logins or use tools like fail2ban, and do not expose PgDog to untrusted networks.

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

The configuration is in `pgdog.toml` and `users.toml`, in `pgdog_conf_dir`. It is validated with `pgdog configcheck` before it is replaced. The logs are in the journal of the `pgdog` service.

Changes are applied with a reload, without closing client connections. `pgdog_listen_addr`, `pgdog_listen_port` and `pgdog_workers` require a restart of the service.

After a failover, some replicas can be left out of the load balancer until PgDog has checked them and their bans have expired. Bans normally expire after `pgdog_ban_timeout` (30 seconds); an unhealthy or lagging replica can remain excluded longer. Reads go to the other eligible nodes in the meantime. If all targets are unavailable, PgDog can clear bans earlier to retry them.

The `add_node.yml` and `remove_node.yml` playbooks update the list of nodes on the whole cluster. New versions are installed by changing `pgdog_version` and running `config_pgcluster.yml` with the tag `pgdog`, which restarts the service.

To inspect a running instance, connect to the admin database:

```bash
psql -h 127.0.0.1 -p 6432 -U admin -d admin -c "SHOW REPLICATION" -c "SHOW POOLS"
```

## Tags

- `pgdog`: all tasks
- `pgdog_install`: install the release
- `pgdog_service`: configure the systemd service
- `pgdog_conf`: update the configuration files
