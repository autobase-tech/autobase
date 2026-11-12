# Ansible Role: prometheus_exporters

Installs and configures [Prometheus exporters](https://prometheus.io/docs/instrumenting/exporters/) on the nodes of the `postgres_cluster` group, and enables the built-in metrics endpoints of the other components, so that a Prometheus server can collect (scrape) the metrics of the cluster and send alerts through Alertmanager.

It can be used together with Netdata, or instead of it (`netdata_install: false`).

## Usage

```yaml
prometheus_exporters_install: true
```

This enables all the endpoints available for the components of the cluster:

| Component | Endpoint | Enabled by |
|-----------|----------|------------|
| System | `http://NODE:9100/metrics` ([node_exporter](https://github.com/prometheus/node_exporter)) | `node_exporter_install` |
| PostgreSQL | `http://NODE:9187/metrics` ([postgres_exporter](https://github.com/prometheus-community/postgres_exporter)) | `postgres_exporter_install` |
| PgBouncer | `http://NODE:9127/metrics` ([pgbouncer_exporter](https://github.com/prometheus-community/pgbouncer_exporter)), and the next ports for the additional `pgbouncer_processes` | `pgbouncer_exporter_install`, if `pgbouncer_install` |
| pgBackRest | `http://NODE:9854/metrics` ([pgbackrest_exporter](https://github.com/woblerr/pgbackrest_exporter)) | `pgbackrest_exporter_install`, if `pgbackrest_install` |
| Patroni | `http(s)://NODE:8008/metrics` (REST API) | always available |
| PgDog | `http://NODE:9090/metrics` (built-in) | `pgdog_openmetrics_port`, if `pgdog_install` |
| etcd | `http://NODE:2381/metrics` (built-in, plain HTTP, no client certificate) | `etcd_metrics_port`, if `dcs_type: etcd` |
| HAProxy | `http://NODE:PORT/metrics` (built-in) | `haproxy_prometheus_port` (opt-in) |

Each exporter can also be enabled or disabled individually, for example `node_exporter_install: false`. Disabled exporters are stopped and removed on the next run. The HAProxy endpoint is opt-in because it requires HAProxy built with the Prometheus exporter (`haproxy -vv` shows "Prometheus exporter").

The exporters are installed from the upstream release archives into `/usr/local/bin`, with the checksums verified, and run as systemd services named after them (`node_exporter`, `postgres_exporter`, `pgbouncer_exporter`, `pgbouncer_exporter-2`, `pgbackrest_exporter`). For offline installations, point `*_package_repo` to a mirror that also contains the checksum file, or set `*_package_checksum: ""`.

The Prometheus server, the scrape configuration (including the discovery of the nodes) and the alerting rules are not managed by this role. See [`files/prometheus_alerts.yml`](files/prometheus_alerts.yml) for example rules.

## Controlling the cardinality

Only the metrics that are needed should be collected:

- `node_exporter_collectors` limits node_exporter to the listed collectors (with `--collector.disable-defaults`).
- `postgres_exporter_collectors` enables or disables [collectors](https://github.com/prometheus-community/postgres_exporter#flags) on top of the exporter defaults. By default, `database_wraparound`, `long_running_transactions` and `postmaster` are added to the default collectors (they are used by the example alerts), and none is disabled. The collectors with the most series are `stat_user_tables` and `statio_user_tables` (per table of the `postgres` database), `settings` (per setting) and `stat_activity` (per database, user, application and state).
- pgbackrest_exporter exports a series per backup kept in the repository for the `pgbackrest_backup_*` metrics (`backup_name` label). The alerts usually need only the `pgbackrest_backup_*last*` and `pgbackrest_backup_since_last_completion_seconds` metrics. Use `pgbackrest_exporter_extra_args`, for example `["--backrest.backup-type=full"]`, or drop the series in Prometheus.
- PgDog, Patroni, etcd and HAProxy expose a fixed set of metrics. The rest can be dropped on the Prometheus side with `metric_relabel_configs`.

```yaml
node_exporter_collectors: [cpu, diskstats, filesystem, loadavg, meminfo, netdev, pressure, time]
postgres_exporter_collectors:
  settings: false
  stat_user_tables: false
  statio_user_tables: false
  stat_statements: true # requires the 'pg_stat_statements' extension in the 'postgres' database
postgres_exporter_extra_args: ["--collector.stat_statements.limit=20"]
```

## Database access

postgres_exporter and pgbouncer_exporter connect through the Unix sockets with the PostgreSQL user `prometheus_exporters_db_user` (`postgres_exporter`). It is created on the primary with the [`pg_monitor`](https://www.postgresql.org/docs/current/predefined-roles.html) role, and added to the `stats_users` of PgBouncer. The password is generated if `prometheus_exporters_db_password` is not defined, and is kept in `/etc/prometheus-exporters/postgres.pass` (mode `0600`) for the next runs. The connection strings are in `/etc/prometheus-exporters/*.env`, readable only by root and the exporters, and are not passed on the command line.

The user is not created on a standby cluster (`patroni_standby_cluster`), which is read-only: create it on the source cluster, and set the same `prometheus_exporters_db_password`.

pgbackrest_exporter runs as `postgres`, to read the pgBackRest configuration and use the same repository access as the backups. It runs on every node, and all nodes report the same backups: aggregate them in the alerts, for example with `max by (stanza)`.

## Network access

The exporters listen on `prometheus_exporters_listen_addr` (all interfaces by default). Their ports are added to the firewall (`firewall_enabled_at_boot`) and, with `cloud_provider`, to the security groups of the cluster network. To allow Prometheus servers outside of that network, set `prometheus_allowed_ips` (comma-separated CIDRs).

To protect the endpoints with TLS or basic authentication, set `prometheus_exporters_web_config` in the [exporter-toolkit format](https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md). It applies to all exporters of this role, but not to the built-in endpoints. The certificate and key files must be readable by the `prometheus` and `postgres` users.

```yaml
prometheus_exporters_web_config:
  basic_auth_users:
    prometheus: "$2y$10$..." # bcrypt hash, e.g. htpasswd -nBC 10 "" | tr -d ':\n'
```

## Role Variables

The variables are defined in [`roles/common/defaults/main.yml`](../common/defaults/main.yml).

| Variable | Default | Description |
|----------|---------|-------------|
| `prometheus_exporters_install` | `false` | Enable all exporters and built-in endpoints available for the cluster |
| `prometheus_exporters_listen_addr` | `"0.0.0.0"` | IP address for the exporters to listen on |
| `prometheus_exporters_user` | `"prometheus"` | System user of the exporters, except pgbackrest_exporter (`postgres`) |
| `prometheus_exporters_conf_dir` | `"/etc/prometheus-exporters"` | Directory for the connection strings and `web.yml` |
| `prometheus_exporters_web_config` | `{}` | TLS and basic authentication of the exporters |
| `prometheus_exporters_db_user` | `"postgres_exporter"` | PostgreSQL user of postgres_exporter and pgbouncer_exporter |
| `prometheus_exporters_db_password` | generated | Its password |
| `node_exporter_install` | `prometheus_exporters_install` | Install node_exporter |
| `node_exporter_version` | see defaults | node_exporter version |
| `node_exporter_port` | `9100` | Port of node_exporter |
| `node_exporter_collectors` | `[]` | Only these collectors, or `[]` for the defaults of node_exporter |
| `node_exporter_extra_args` | `[]` | Other command-line flags |
| `postgres_exporter_install` | `prometheus_exporters_install` | Install postgres_exporter |
| `postgres_exporter_version` | see defaults | postgres_exporter version |
| `postgres_exporter_port` | `9187` | Port of postgres_exporter |
| `postgres_exporter_collectors` | see defaults | Collectors to enable (`true`) or disable (`false`) |
| `postgres_exporter_extra_args` | `[]` | Other command-line flags |
| `pgbouncer_exporter_install` | `prometheus_exporters_install` and `pgbouncer_install` | Install pgbouncer_exporter |
| `pgbouncer_exporter_version` | see defaults | pgbouncer_exporter version |
| `pgbouncer_exporter_port` | `9127` | Port of the first pgbouncer_exporter |
| `pgbouncer_exporter_extra_args` | `[]` | Other command-line flags |
| `pgbackrest_exporter_install` | `prometheus_exporters_install` and `pgbackrest_install` | Install pgbackrest_exporter |
| `pgbackrest_exporter_version` | see defaults | pgbackrest_exporter version |
| `pgbackrest_exporter_port` | `9854` | Port of pgbackrest_exporter |
| `pgbackrest_exporter_collect_interval` | `600` | Seconds between the `pgbackrest info` calls |
| `pgbackrest_exporter_extra_args` | `[]` | Other command-line flags |
| `*_package_repo` | GitHub release | URL of the release archive |
| `*_package_checksum` | `sha256:<checksum file URL>` | Checksum of the archive, or `""` to skip the verification |
| `pgdog_openmetrics_port` | `9090` with `prometheus_exporters_install` | Port of the PgDog OpenMetrics endpoint, or `""` |
| `etcd_metrics_port` | `2381` with `prometheus_exporters_install` | Port of the etcd metrics endpoint, or `""` |
| `haproxy_prometheus_port` | `""` | Port of the HAProxy Prometheus endpoint, or `""` |
| `prometheus_allowed_ips` | `""` | CIDRs of Prometheus servers outside of the cluster network (cloud security groups) |

## Operations

New versions are installed by changing `*_version` and running `config_pgcluster.yml` with the tag `prometheus_exporters`. Only the exporters whose binary or configuration has changed are restarted. The exporters on a node added by `add_node.yml` are configured like on the other nodes.

The etcd metrics endpoint is configured when etcd is deployed (`ETCD_LISTEN_METRICS_URLS` in `/etc/etcd/etcd.conf`). On an existing cluster, add this setting and restart etcd one member at a time.

## Tags

- `prometheus_exporters`: all tasks
- `prometheus_exporters_install`: install the release archives
- `prometheus_exporters_conf`: configure the systemd services and the connections
- `prometheus_exporters_db_user`: create the PostgreSQL user

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
