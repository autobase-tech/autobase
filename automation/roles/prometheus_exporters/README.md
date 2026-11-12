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
| Consul | `http://NODE:9107/metrics` ([consul_exporter](https://github.com/prometheus/consul_exporter)) | `consul_exporter_install`, if `dcs_type: consul` |
| Patroni | `http(s)://NODE:8008/metrics` (REST API) | always available |
| PgDog | `http://NODE:9090/metrics` (built-in) | `pgdog_openmetrics_port`, if `pgdog_install` |
| etcd | `http://NODE:2381/metrics` (built-in, plain HTTP, no client certificate) | `etcd_metrics_port`, if `dcs_type: etcd` |
| HAProxy | `http://NODE:PORT/metrics` (built-in) | `haproxy_prometheus_port` (opt-in) |

Each exporter can also be enabled or disabled individually, for example `node_exporter_install: false`. Disabled exporters are stopped and removed on the next run. The HAProxy endpoint is opt-in because it requires HAProxy built with the Prometheus exporter (`haproxy -vv` shows "Prometheus exporter").

The exporters are installed from the upstream release archives into `/usr/local/bin`, with the checksums verified, and run as systemd services named after them (`node_exporter`, `postgres_exporter`, `pgbouncer_exporter`, `pgbouncer_exporter-2`, `pgbackrest_exporter`, `consul_exporter`). For offline installations, point `*_package_repo` to a mirror that also contains the checksum file, or set `*_package_checksum: ""`.

The Prometheus server, the scrape configuration (including the discovery of the nodes) and the alerting rules are not managed by this role. See [Alerts](#alerts) for example alerting rules, and [Collecting only the needed metrics](#collecting-only-the-needed-metrics) to control the cardinality.

## Database access

postgres_exporter and pgbouncer_exporter connect through the Unix sockets with the PostgreSQL user `prometheus_exporters_db_user` (`postgres_exporter`). It is created on the primary with the [`pg_monitor`](https://www.postgresql.org/docs/current/predefined-roles.html) role, and added to the `stats_users` of PgBouncer. The password is generated if `prometheus_exporters_db_password` is not defined, and is kept in `/etc/prometheus-exporters/postgres.pass` (mode `0600`) for the next runs. The connection strings are in `/etc/prometheus-exporters/*.env`, readable only by root and the exporters, and are not passed on the command line.

postgres_exporter connects to the database `postgres_exporter_dbname` (`postgres`). The instance-wide metrics, such as `pg_stat_database`, the database sizes, the transaction ID wraparound, the replication and the WAL, cover all databases. The per-table and per-index metrics (`stat_user_tables`, `statio_user_tables`, `statio_user_indexes`) only cover the database the exporter connects to: set `postgres_exporter_dbname` to the main database of the application to get them. The user needs the `CONNECT` privilege on it, which is granted to `PUBLIC` by default.

The user is not created on a standby cluster (`patroni_standby_cluster`), which is read-only: create it on the source cluster, and set the same `prometheus_exporters_db_password`.

pgbackrest_exporter runs as `postgres`, to read the pgBackRest configuration and use the same repository access as the backups. It runs on every node, and all nodes report the same backups: aggregate them in the alerts, for example with `max by (stanza)`.

## Consul

The HTTP API of the Consul agents listens on `127.0.0.1` only, so its built-in metrics cannot be scraped remotely. consul_exporter runs on every node and queries the local agent (`consul_exporter_server`, like Patroni), over HTTPS when `consul_tls_enable` is `true`, with a copy of the CA certificate of Consul in `/etc/prometheus-exporters/consul-ca.crt` (the Consul configuration directory is only readable by the `consul` user). With `consul_tls_verify_incoming`, it also uses the client certificate of Consul and runs as the `consul` user, which can read its key.

All nodes report the cluster-wide metrics: the Raft leader and peers, the members, and the health of all the services in the catalog. Aggregate them in the alerts. With a Consul cluster shared by many Postgres clusters (`dcs_exists`), the catalog can be large: `consul_exporter_agent_only: true` reports only the services of the local agent, but it also disables the Raft and members metrics.

If the ACLs deny access by default, set `consul_exporter_acl_token` to a token with read access to the nodes, services, agent and operator. It is passed in an environment file, not on the command line.

## Network access

The exporters listen on `prometheus_exporters_listen_addr` (all interfaces by default). Their ports are added to the firewall (`firewall_enabled_at_boot`) and, with `cloud_provider`, to the security groups of the cluster network. To allow Prometheus servers outside of that network, set `prometheus_allowed_ips` (comma-separated CIDRs).

To protect the endpoints with TLS or basic authentication, set `prometheus_exporters_web_config` in the [exporter-toolkit format](https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md). It applies to all exporters of this role, but not to the built-in endpoints. The certificate and key files must be readable by the `prometheus` and `postgres` users.

```yaml
prometheus_exporters_web_config:
  basic_auth_users:
    prometheus: "$2y$10$..." # bcrypt hash, e.g. htpasswd -nBC 10 "" | tr -d ':\n'
```

## Alerts

[`files/prometheus_alerts.yml`](files/prometheus_alerts.yml) contains example alerting rules for these metrics. They cover the availability, the high availability, the safety of the data and the capacity of the cluster. The file is not deployed: copy it to the `rule_files` of your Prometheus, adapt the thresholds to your workload, backup schedule and alert routing, and validate it with `promtool check rules prometheus_alerts.yml`.

The alerts use the `instance` label of the targets and the labels of the exporters (`datname`, `scope`, `stanza`...). Some metrics are reported by all nodes for the whole cluster (pgBackRest, Consul): the alerts aggregate them, so they fire once.

| Group | Alert | Severity | Detects |
|-------|-------|----------|---------|
| node | MetricsTargetDown | critical | A metrics endpoint does not respond |
| node | NodeFilesystemAlmostFull | critical | Less than 10% of disk space left |
| node | NodeFilesystemFillingUp | warning | A disk will be full within 24 hours, at the current rate |
| node | NodeFilesystemInodesAlmostExhausted | critical | Less than 10% of inodes left |
| node | NodeMemoryLow | warning | Less than 5% of memory available |
| node | NodeOomKill | critical | The OOM killer terminated a process (a PostgreSQL backend means a restart of all connections) |
| node | NodeClockNotSynchronised | warning | The clock is not synchronised |
| patroni | PatroniPostgresNotRunning | critical | PostgreSQL is not running on a node |
| patroni | PatroniClusterUnlocked | critical | The cluster has no leader |
| patroni | PatroniLeaderChanged | warning | Failover or switchover (new timeline) |
| patroni | PatroniFrequentLeaderChanges | critical | More than 2 leader changes in an hour |
| patroni | PatroniDcsUnreachable | warning | Patroni has not reached the DCS for 5 minutes |
| patroni | PatroniReplicaNotStreaming | warning | A replica does not stream from the primary |
| patroni | PatroniPaused | warning | Maintenance mode for more than an hour (no automatic failover) |
| patroni | PatroniPendingRestart | info | A restart is needed to apply the configuration |
| patroni | PatroniNoSynchronousStandby | critical | Commented out, for `synchronous_mode: true` only |
| postgres | PostgresDown | critical | postgres_exporter cannot connect to PostgreSQL |
| postgres | PostgresExporterCollectorFailing | warning | A collector fails, leaving gaps in the metrics |
| postgres | PostgresRestarted | warning | The postmaster restarted (e.g. after a crash), without failover |
| postgres | PostgresTxidWraparound | warning, critical | Transaction ID age above 500 million and 1 billion |
| postgres | PostgresMultixactWraparound | warning | Multixact ID age above 1 billion |
| postgres | PostgresReplicationLag | warning | A replica is more than 5 minutes behind |
| postgres | PostgresInactiveReplicationSlot | warning | An inactive slot on the primary retains WAL |
| postgres | PostgresReplicationSlotRetainsWal | warning | A slot retains more than 10 GiB of WAL |
| postgres | PostgresWalArchivingFailing | critical | `archive_command` fails |
| postgres | PostgresLongRunningTransaction | warning | A transaction runs for more than an hour |
| postgres | PostgresIdleInTransaction | warning | A session is idle in transaction for more than 5 minutes |
| postgres | PostgresDeadlocks | warning | More than 5 deadlocks in an hour |
| postgres | PostgresTooManyConnections | warning, critical | More than 80% and 90% of `max_connections` |
| postgres | PostgresTooManyLocks | warning | More than 20% of the lock table |
| pgbouncer | PgBouncerDown | critical | pgbouncer_exporter cannot connect to PgBouncer |
| pgbouncer | PgBouncerClientsWaiting | warning | Clients wait more than 10 seconds for a server connection |
| pgbouncer | PgBouncerClientConnectionsNearLimit | critical | More than 90% of `max_client_conn` |
| pgbackrest | PgBackRestInfoFailing | warning | `pgbackrest info` fails |
| pgbackrest | PgBackRestStanzaError | critical | The stanza has an error status |
| pgbackrest | PgBackRestBackupError | critical | The last backup contains page checksum errors |
| pgbackrest | PgBackRestNoRecentBackup | warning, critical | No backup of any type for 1 and 2 days |
| pgbackrest | PgBackRestNoRecentFullBackup | warning | No full backup for 8 days |
| etcd | EtcdNoLeader | critical | A member has no leader |
| etcd | EtcdFrequentLeaderChanges | warning | More than 3 leader changes in an hour |
| etcd | EtcdDatabaseQuotaAlmostFull | critical | More than 80% of the quota (at 100%, Patroni cannot keep the leader lock) |
| etcd | EtcdSlowWalFsync | warning | WAL fsync p99 above 0.5 seconds |
| consul | ConsulAgentDown | critical | The local agent does not respond (Patroni loses the DCS on this node) |
| consul | ConsulNoLeader | critical | The Consul cluster has no Raft leader |
| consul | ConsulMemberFailed | warning | A member has failed |
| consul | ConsulNoHealthyPrimaryService | critical | No node passes the checks of the `<cluster>-master` service |
| consul | ConsulPgDogServiceUnhealthy | warning | PgDog on a node fails its Consul check |
| haproxy | HAProxyNoPrimary | critical | No primary in the `master` backend |

The per-table metrics (dead tuples, last autovacuum and autoanalyze) are collected for one database, `postgres_exporter_dbname`; the example alerts do not use them. \
Not covered by the exporters: the per-table metrics of the other databases, the table and index bloat, the exhaustion of the sequences, and the data checksum failures.

## Collecting only the needed metrics

The exporters expose much more than the alerts use. If the Prometheus server is shared, or if the metrics are only used for alerting, limit them at two levels.

### 1. In Autobase: select the collectors

This removes the metrics at the source and reduces the load of the exporters.

- `node_exporter_collectors` limits node_exporter to the listed collectors (with `--collector.disable-defaults`).
- `postgres_exporter_collectors` enables or disables [collectors](https://github.com/prometheus-community/postgres_exporter#flags) on top of the exporter defaults. By default, `database_wraparound`, `long_running_transactions` and `postmaster` are added (they are used by the alerts), and none is disabled. The collectors with the most series are `stat_user_tables` and `statio_user_tables` (per table of the `postgres_exporter_dbname` database), `settings` (per setting) and `stat_activity` (per database, user, application and state).
- pgbackrest_exporter exports a series per backup kept in the repository for the `pgbackrest_backup_*` metrics (`backup_name` label); the alerts only need the `*last*` and `since_last_completion` metrics. `pgbackrest_exporter_extra_args`, for example `["--backrest.backup-type=full"]`, limits the backup types.
- PgBouncer, Patroni, etcd, Consul, PgDog and HAProxy cannot select their metrics: use the second level.

The variables to collect only the data used by the example alerts, for example in the `group_vars` of the cluster:

```yaml
prometheus_exporters_install: true

# node_exporter: only the collectors of the alerts.
# filesystem (disk space, inodes), meminfo (memory), vmstat (OOM kills), timex (clock)
node_exporter_collectors: [filesystem, meminfo, vmstat, timex]
node_exporter_extra_args:
  - "--collector.vmstat.fields=^oom_kill$" # only node_vmstat_oom_kill
  - "--web.disable-exporter-metrics" # without the go_*, process_* and promhttp_* metrics of the exporter

# postgres_exporter: only the collectors of the alerts.
# The dictionary replaces the default one, so it lists the collectors enabled by Autobase too.
postgres_exporter_collectors:
  database_wraparound: true # PostgresTxidWraparound, PostgresMultixactWraparound
  long_running_transactions: true # PostgresLongRunningTransaction
  postmaster: true # PostgresRestarted
  # kept enabled (exporter defaults) for the alerts: locks, replication, replication_slots, settings,
  # stat_activity, stat_archiver, stat_database
  database: false
  stat_bgwriter: false
  stat_progress_vacuum: false
  stat_replication: false
  stat_user_tables: false
  statio_user_tables: false
  wal: false
# Without the legacy built-in metrics (pg_stat_database_conflicts_*, pg_static), which are not collectors.
# pg_up and the collectors are not affected.
postgres_exporter_extra_args: ["--disable-default-metrics"]

# pgbouncer_exporter, pgbackrest_exporter, consul_exporter, Patroni, etcd, and PgDog cannot select their metrics:
# keep their defaults, and use the keep lists of the second level.
```

The exporters still expose more metrics than the alerts use: a collector exposes all its metrics (for example `meminfo` exposes all the fields of `/proc/meminfo`), and pgbouncer_exporter, pgbackrest_exporter, consul_exporter, Patroni and etcd cannot select them. Only the keep lists of the second level reduce the stored metrics to the exact list.

To add metrics instead, for example the statistics of the queries:

```yaml
postgres_exporter_collectors:
  database_wraparound: true
  long_running_transactions: true
  postmaster: true
  stat_statements: true # requires the 'pg_stat_statements' extension in the 'postgres_exporter_dbname' database
postgres_exporter_extra_args: ["--collector.stat_statements.limit=20"]
```

### 2. In Prometheus: keep only the metrics used by the alerts

`metric_relabel_configs` with `action: keep` drops the other series before they are stored. The exporters still send them, but they do not use any space in the TSDB. The `up` series is created by Prometheus and is not affected.

| Job | Metrics used by the alerts |
|-----|----------------------------|
| node_exporter | `node_filesystem_avail_bytes`, `node_filesystem_size_bytes`, `node_filesystem_files`, `node_filesystem_files_free`, `node_filesystem_readonly`, `node_memory_MemAvailable_bytes`, `node_memory_MemTotal_bytes`, `node_vmstat_oom_kill`, `node_timex_sync_status`, `node_timex_maxerror_seconds` |
| postgres_exporter | `pg_up`, `pg_scrape_collector_success`, `pg_postmaster_start_time_seconds`, `pg_database_wraparound_age_datfrozenxid_seconds`, `pg_database_wraparound_age_datminmxid_seconds`, `pg_replication_is_replica`, `pg_replication_lag_seconds`, `pg_replication_slots_active`, `pg_replication_slots_pg_wal_lsn_diff`, `pg_stat_archiver_failed_count`, `pg_long_running_transactions_oldest_timestamp_seconds`, `pg_stat_activity_count`, `pg_stat_activity_max_tx_duration`, `pg_stat_database_deadlocks`, `pg_locks_count`, `pg_settings_max_connections`, `pg_settings_max_locks_per_transaction` |
| pgbouncer_exporter | `pgbouncer_up`, `pgbouncer_pools_client_maxwait_seconds`, `pgbouncer_pools_client_active_connections`, `pgbouncer_pools_client_waiting_connections`, `pgbouncer_config_max_client_connections` |
| pgbackrest_exporter | `pgbackrest_exporter_status`, `pgbackrest_stanza_status`, `pgbackrest_backup_last_error_status`, `pgbackrest_backup_since_last_completion_seconds` |
| Patroni | `patroni_postgres_running`, `patroni_cluster_unlocked`, `patroni_postgres_timeline`, `patroni_dcs_last_seen`, `patroni_replica`, `patroni_postgres_streaming`, `patroni_is_paused`, `patroni_pending_restart` (and `patroni_sync_standby` for the commented alert) |
| etcd | `etcd_server_has_leader`, `etcd_server_leader_changes_seen_total`, `etcd_mvcc_db_total_size_in_bytes`, `etcd_server_quota_backend_bytes`, `etcd_disk_wal_fsync_duration_seconds_bucket` |
| consul_exporter | `consul_up`, `consul_raft_leader`, `consul_serf_lan_member_status`, `consul_catalog_service_node_healthy` |
| HAProxy | `haproxy_backend_active_servers` |

Example scrape configuration; replace `static_configs` with the service discovery of your environment:

```yaml
scrape_configs:
  - job_name: node_exporter
    static_configs:
      - targets: ["pgnode01:9100", "pgnode02:9100", "pgnode03:9100"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: node_filesystem_(avail_bytes|size_bytes|files|files_free|readonly)|node_memory_(MemAvailable|MemTotal)_bytes|node_vmstat_oom_kill|node_timex_(sync_status|maxerror_seconds)
        action: keep

  - job_name: postgres_exporter
    static_configs:
      - targets: ["pgnode01:9187", "pgnode02:9187", "pgnode03:9187"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: >-
          pg_up|pg_scrape_collector_success|pg_postmaster_start_time_seconds|pg_database_wraparound_age_dat(frozenxid|minmxid)_seconds|pg_replication_(is_replica|lag_seconds)|pg_replication_slots_(active|pg_wal_lsn_diff)|pg_stat_archiver_failed_count|pg_long_running_transactions_oldest_timestamp_seconds|pg_stat_activity_(count|max_tx_duration)|pg_stat_database_deadlocks|pg_locks_count|pg_settings_(max_connections|max_locks_per_transaction)
        action: keep

  - job_name: pgbouncer_exporter # one target per PgBouncer process: 9127, 9128...
    static_configs:
      - targets: ["pgnode01:9127", "pgnode02:9127", "pgnode03:9127"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: pgbouncer_up|pgbouncer_pools_client_(maxwait_seconds|active_connections|waiting_connections)|pgbouncer_config_max_client_connections
        action: keep

  - job_name: pgbackrest_exporter
    static_configs:
      - targets: ["pgnode01:9854", "pgnode02:9854", "pgnode03:9854"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: pgbackrest_exporter_status|pgbackrest_stanza_status|pgbackrest_backup_last_error_status|pgbackrest_backup_since_last_completion_seconds
        action: keep

  - job_name: patroni
    scheme: https # http if 'tls_cert_generate: false'
    tls_config:
      ca_file: /etc/prometheus/autobase-ca.crt # the CA of the cluster ('tls_dir'/'tls_ca_cert')
    static_configs:
      - targets: ["pgnode01:8008", "pgnode02:8008", "pgnode03:8008"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: patroni_(postgres_running|cluster_unlocked|postgres_timeline|dcs_last_seen|replica|postgres_streaming|is_paused|pending_restart|sync_standby)
        action: keep

  - job_name: etcd # with 'dcs_type: etcd'
    static_configs:
      - targets: ["pgnode01:2381", "pgnode02:2381", "pgnode03:2381"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: etcd_server_(has_leader|leader_changes_seen_total|quota_backend_bytes)|etcd_mvcc_db_total_size_in_bytes|etcd_disk_wal_fsync_duration_seconds_bucket
        action: keep

  - job_name: consul_exporter # with 'dcs_type: consul'
    static_configs:
      - targets: ["pgnode01:9107", "pgnode02:9107", "pgnode03:9107"]
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: consul_(up|raft_leader|serf_lan_member_status|catalog_service_node_healthy)
        action: keep
```

Notes:

- The keep lists drop the metrics of the dashboards. Add the metrics you need, or skip the keep list for the jobs whose dashboards you use.
- With the keep lists, the cardinality mostly depends on the number of databases (`datname`), of PgBouncer pools (`database`, `user`), of replication slots, of filesystems, and on the activity (`pg_stat_activity_*` has a series per database, user, application and state).
- The `settings` collector of postgres_exporter cannot select the settings: only the two used by the alerts are kept by the Prometheus keep list.
- When you add or change an alert, update the keep lists. The metrics used by the rules can be listed with `grep -o 'expr:.*' prometheus_alerts.yml`.

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
| `postgres_exporter_dbname` | `"postgres"` | Database to connect to (per-table metrics are collected for this database only) |
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
| `consul_exporter_install` | `prometheus_exporters_install` and `dcs_type: consul` | Install consul_exporter |
| `consul_exporter_version` | see defaults | consul_exporter version |
| `consul_exporter_port` | `9107` | Port of consul_exporter |
| `consul_exporter_server` | `patroni_consul_host` or `127.0.0.1:8500` | Address of the local Consul agent |
| `consul_exporter_acl_token` | `""` | ACL token, if the ACLs deny access by default |
| `consul_exporter_agent_only` | `false` | Report only the services of the local agent (disables the Raft and members metrics) |
| `consul_exporter_extra_args` | `[]` | Other command-line flags |
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
