# Ansible Role: patroni

This role installs and configures [Patroni](https://github.com/patroni/patroni), a high-availability solution for PostgreSQL that manages PostgreSQL configuration and provides automatic failover in PostgreSQL clusters.

## Role Variables

### Core Configuration

| Variable                           | Default              | Description                                                                                                       |
| ---------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `patroni_cluster_name`             | `"postgres-cluster"` | PostgreSQL cluster name (must be unique for each cluster)                                                         |
| `patroni_superuser_username`       | `"postgres"`         | PostgreSQL superuser username                                                                                     |
| `patroni_superuser_password`       | `""`                 | PostgreSQL superuser password (auto-generated if empty)                                                           |
| `patroni_replication_username`     | `"replicator"`       | PostgreSQL replication user username                                                                              |
| `patroni_replication_password`     | `""`                 | PostgreSQL replication user password (auto-generated if empty)                                                    |
| `patroni_superuser_auth_options`   | `[]`                 | Extra libpq auth options for superuser (e.g., sslmode, sslrootcert). Defaults depend on tls_cert_generate.        |
| `patroni_replication_auth_options` | `[]`                 | Extra libpq auth options for replication user (e.g., sslmode, sslrootcert). Defaults depend on tls_cert_generate. |
| `patroni_switchover_candidate_name` | `""`                | Optional Patroni node name to promote during a switchover.                                                        |
| `patroni_failover_candidate_name`  | `""`                 | Optional Patroni node name to promote during a failover.                                                          |
| `patroni_failover_force`           | `false`              | Allow failover when a healthy Patroni leader is detected.                                                         |
| `patroni_reinit_member_name`        | `""`                 | Patroni replica node name to rebuild with `reinit_pgcluster`.                                                   |
| `patroni_reinit_wait`               | `false`              | Wait for the reinitialized replica to become healthy, up to `cluster_restore_timeout`.                          |
| `patroni_restart_node_name`          | `""`                 | Patroni node name to restart with `restart_pgnode`.                                    |
| `patroni_stop_node_name`             | `""`                 | Patroni node name to stop with `stop_pgnode`.                                                                   |
| `patroni_start_node_name`            | `""`                 | Patroni node name to start with `start_pgnode`.                                                                 |

### Installation Configuration

| Variable                        | Default         | Description                                                     |
| ------------------------------- | --------------- | --------------------------------------------------------------- |
| `patroni_install_version`       | `"latest"`      | Patroni version to install when using pip                       |
| `patroni_installation_method`   | `"deb"`/`"rpm"` | Installation method for Patroni (`deb`, `rpm`, or `pip`)        |
| `patroni_latest_requirements`   | `false`         | Use latest requirements.txt from master branch. When using pip. |
| `patroni_pip_package_repo`      | `[]`            | List of custom Patroni package repository URLs                  |
| `patroni_pip_requirements_repo` | `[]`            | List of custom requirements repository URLs                     |
| `patroni_deb_package_repo`      | `[]`            | List of custom DEB package repository URLs                      |
| `patroni_rpm_package_repo`      | `[]`            | List of custom RPM package repository URLs                      |

### Network Configuration

| Variable                       | Default                | Description                                                      |
| ------------------------------ | ---------------------- | ---------------------------------------------------------------- |
| `patroni_bind_address`         | `"{{ bind_address }}"` | IP address for PostgreSQL connections (defaults to bind_address) |
| `patroni_restapi_connect_addr` | `""`                   | Optional hostname for REST API (otherwise IP is used).           |
| `postgresql_connect_addr`      | `""`                   | Optional hostname for DB connections (otherwise IP is used).     |

### REST API Configuration

| Variable                             | Default                 | Description                                 |
| ------------------------------------ | ----------------------- | ------------------------------------------- |
| `patroni_restapi_listen_addr`        | `"0.0.0.0"`             | REST API listen address                     |
| `patroni_restapi_port`               | `8008`                  | REST API port                               |
| `patroni_restapi_username`           | `"patroni"`             | REST API username                           |
| `patroni_restapi_password`           | `""`                    | REST API password (auto-generated if empty) |
| `patroni_restapi_request_queue_size` | `5`                     | REST API request queue size                 |
| `patroni_restapi_protocol`           | `https`                 | REST API protocol.                          |
| `patroni_restapi_certfile`           | `"/etc/tls/server.crt"` | REST API TLS cert path (when HTTPS).        |
| `patroni_restapi_keyfile`            | `"/etc/tls/server.key"` | REST API TLS key path (when HTTPS).         |
| `patroni_restapi_cafile`             | `"/etc/tls/ca.crt"`     | REST API CA path (when HTTPS).              |

### Cluster Behavior Configuration

| Variable                                              | Default   | Description                                                     |
| ----------------------------------------------------- | --------- | --------------------------------------------------------------- |
| `patroni_ttl`                                         | `30`      | TTL for leader key in DCS                                       |
| `patroni_loop_wait`                                   | `10`      | Sleep time between runs                                         |
| `patroni_retry_timeout`                               | `10`      | Timeout for retrying failed operations                          |
| `patroni_master_start_timeout`                        | `300`     | Timeout for master startup                                      |
| `patroni_maximum_lag_on_failover`                     | `1048576` | Maximum lag in bytes for failover eligibility                   |
| `patroni_maximum_lag_on_replica`                      | `"100MB"` | Maximum lag for read-only queries                               |
| `patroni_postgresql_use_pg_rewind`                    | `true`    | Enable pg_rewind for faster recovery                            |
| `patroni_remove_data_directory_on_rewind_failure`     | `false`   | Remove data directory on rewind failure                         |
| `patroni_remove_data_directory_on_diverged_timelines` | `false`   | Remove data directory on diverged timelines                     |
| `patroni_use_unix_socket`                             | `true`    | Prefer unix socket for local cluster connections.               |
| `patroni_use_unix_socket_repl`                        | `true`    | Prefer unix socket for replication user connections.            |
| `synchronous_mode`                                    | `false`   | Enable synchronous replication.                                 |
| `synchronous_mode_strict`                             | `false`   | If true, block writes when no synchronous replica is available. |
| `synchronous_node_count`                              | `1`       | Number of synchronous standbys.                                 |
| `patroni_failsafe_mode`                               | `true`    | Enables Patroni DCS failsafe mode.                              |

### Bootstrap Configuration

| Variable                           | Default        | Description                                                        |
| ---------------------------------- | -------------- | ------------------------------------------------------------------ |
| `patroni_cluster_bootstrap_method` | `"initdb"`     | Bootstrap method (`initdb`, `wal-g`, `pgbackrest`, `pg_probackup`) |
| `patroni_create_replica_methods`   | `[basebackup]` | List of replica creation methods.                                  |
| `disable_archive_command` | `false` | Disable WAL archiving during and after recovery. Set to `true` when cloning into an independent cluster. |

### Watchdog Configuration

| Variable                  | Default           | Description                                    |
| ------------------------- | ----------------- | ---------------------------------------------- |
| `patroni_watchdog_mode`   | `"automatic"`     | Watchdog mode (`automatic`, `off`, `required`) |
| `patroni_watchdog_device` | `"/dev/watchdog"` | Watchdog device path.                          |

### Logging Configuration

| Variable                                 | Default                                    | Description                             |
| ---------------------------------------- | ------------------------------------------ | --------------------------------------- |
| `patroni_log_destination`                | `"logfile"`                                | Log destination (`logfile` or `stderr`) |
| `patroni_log_dir`                        | `"/var/log/patroni"`                       | Patroni log directory                   |
| `patroni_log_level`                      | `"warning"`                                | Patroni log level                       |
| `patroni_log_traceback_level`            | `"error"`                                  | Patroni log traceback level             |
| `patroni_log_format`                     | `"%(asctime)s %(levelname)s: %(message)s"` | Patroni log format                      |
| `patroni_log_dateformat`                 | `""`                                       | Patroni log date format                 |
| `patroni_log_max_queue_size`             | `1000`                                     | Maximum log queue size                  |
| `patroni_log_file_num`                   | `4`                                        | Number of log files to rotate           |
| `patroni_log_file_size`                  | `25000000`                                 | Log file size in bytes                  |
| `patroni_log_loggers_patroni_postmaster` | `"warning"`                                | Log level for patroni.postmaster logger |
| `patroni_log_loggers_urllib3`            | `"warning"`                                | Log level for urllib3 logger            |

### Callbacks Configuration

| Variable            | Default | Description                                      |
| ------------------- | ------- | ------------------------------------------------ |
| `patroni_callbacks` | `[]`    | List of callback configurations (action:script). |

### Standby cluster configuration

| Variable                                           | Default  | Description                                                                         |
| -------------------------------------------------- | -------- | ----------------------------------------------------------------------------------- |
| `patroni_standby_cluster`                          | `{}`     | Standby cluster configuration. See below.                                           |
| `patroni_standby_cluster.host`                     | `""`     | IP address of main cluster host                                                     |
| `patroni_standby_cluster.port`                     | `"5432"` | port of main cluster host                                                           |
| `patroni_standby_cluster.primary_slot_name`        | `""`     | which slot on the remote primary to use for replication (optional)                  |
| `patroni_standby_cluster.restore_command`          | `""`     | command to restore WAL records from the remote primary to standby leader (optional) |
| `patroni_standby_cluster.recovery_min_apply_delay` | `""`     | how long to wait before actually apply WAL records on a standby leader (optional)   |
| `patroni_standby_cluster.create_replica_methods`   | `[]`     | methods to create the standby leader, e.g. `["pgbackrest"]` (optional)              |

Requirements:

1. the cluster name for standby cluster must be unique (see 'patroni_cluster_name' variable)
2. the IP addresses (or network) of the standby cluster servers must be added to the pg_hba.conf of the Main Cluster (see 'postgresql_pg_hba' variable).

### Slots Configuration

| Variable        | Default | Description                                                                            |
| --------------- | ------- | -------------------------------------------------------------------------------------- |
| `patroni_slots` | `[]`    | Permanent replication slots. These slots will be preserved during switchover/failover. |

Example:

```yaml
patroni_slots:
  - slot: "logical_replication_slot" # the name of the permanent replication slot.
    type: "logical" # the type of slot. Could be 'physical' or 'logical' (if the slot is logical, you have to define 'database' and 'plugin').
    plugin: "pgoutput" # the plugin name for the logical slot.
    database: "postgres" # the database name where logical slots should be created.
```

### DCS Integration (etcd)

| Variable                 | Default                              | Description                               |
| ------------------------ | ------------------------------------ | ----------------------------------------- |
| `patroni_etcd_hosts`     | `[]`                                 | List of external etcd servers (host:port) |
| `patroni_etcd_namespace` | `"service"`                          | etcd namespace prefix                     |
| `patroni_etcd_username`  | `""`                                 | etcd authentication username              |
| `patroni_etcd_password`  | `""`                                 | etcd authentication password              |
| `patroni_etcd_protocol`  | `"https"`                            | etcd protocol (`http` or `https`)         |
| `patroni_etcd_cacert`    | `"/etc/patroni/tls/etcd/ca.crt"`     | etcd CA certificate path                  |
| `patroni_etcd_cert`      | `"/etc/patroni/tls/etcd/server.crt"` | etcd client certificate path              |
| `patroni_etcd_key`       | `"/etc/patroni/tls/etcd/server.key"` | etcd client key path                      |

### DCS Integration (consul)

| Variable                | Default                                | Description                    |
| ----------------------- | -------------------------------------- | ------------------------------ |
| `patroni_consul_host`   | `"127.0.0.1:8500"`                     | Consul host and port           |
| `patroni_consul_cacert` | `"/etc/patroni/tls/consul/ca.crt"`     | Consul CA certificate path     |
| `patroni_consul_cert`   | `"/etc/patroni/tls/consul/server.crt"` | Consul client certificate path |
| `patroni_consul_key`    | `"/etc/patroni/tls/consul/server.key"` | Consul client key path         |

### PostgreSQL Configuration

| Variable                                   | Default                                                                                                                                                                                                  | Description                                                                  |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `postgresql_bin_dir`                       | `/usr/lib/postgresql/{{ postgresql_version }}/bin` (Debian) / `"/usr/pgsql-{{ postgresql_version }}/bin"` (RedHat)                                                                                       | PostgreSQL binary directory.                                                 |
| `postgresql_home_dir`                      | `"/var/lib/postgresql"` (Debian) / `"/var/lib/pgsql"` (RedHat)                                                                                                                                           | PostgreSQL OS home directory.                                                |
| `postgresql_data_dir`                      | `/pgdata/{{ postgresql_version }}/main` (if cloud_provider is specified) / else `/var/lib/postgresql/{{ postgresql_version }}/main` (Debian) / `"/var/lib/pgsql/{{ postgresql_version }}/data"` (RedHat) | PostgreSQL data directory.                                                   |
| `postgresql_wal_dir`                       | `""`                                                                                                                                                                                                     | Custom WAL directory. If defined, symlink will be created (optional).        |
| `postgresql_conf_dir`                      | `/etc/postgresql/{{ postgresql_version }}/main` (Debian) / `"{{ postgresql_data_dir }}` (RedHat)                                                                                                         | Path to PostgreSQL configuration directory.                                  |
| `postgresql_log_dir`                       | `"/var/log/postgresql"`                                                                                                                                                                                  | PostgreSQL log directory.                                                    |
| `postgresql_unix_socket_dir`               | `"/var/run/postgresql"`                                                                                                                                                                                  | Directory for PostgreSQL unix sockets.                                       |
| `postgresql_listen_addr`                   | "`0.0.0.0"`                                                                                                                                                                                              | Listen address used in Patroni postgresql.listen.                            |
| `postgresql_port`                          | `5432`                                                                                                                                                                                                   | Cluster port used in listen/connect_address.                                 |
| `postgresql_encoding`                      | "`UTF8`"                                                                                                                                                                                                 | Passed to initdb during bootstrap.                                           |
| `postgresql_locale`                        | "`en_US.UTF-8`"                                                                                                                                                                                          | Passed to initdb during bootstrap.                                           |
| `postgresql_locale_provider`               | `""`                                                                                                                                                                                                     | Passed to initdb as `--locale-provider` if set: `libc`, `icu` or `builtin`.  |
| `postgresql_icu_locale`                    | `""`                                                                                                                                                                                                     | Passed to initdb as `--icu-locale`. Required for the `icu` provider.         |
| `postgresql_builtin_locale`                | "`C.UTF-8`"                                                                                                                                                                                              | Passed to initdb as `--builtin-locale` for the `builtin` provider.           |
| `postgresql_data_checksums`                | `true`                                                                                                                                                                                                   | Enables data checksums during initdb.                                        |
| `postgresql_password_encryption_algorithm` | "`scram-sha-256`"                                                                                                                                                                                        | Default auth method in generated pg_hba.                                     |
| `postgresql_parameters`                    | [...]                                                                                                                                                                                                    | Cluster-wide parameters stored in DCS (bootstrap.dcs.postgresql.parameters). |
| `postgresql_parameters_overrides`          | `[]`                                                                                                                                                                                                     | Additional cluster-wide DCS parameters merged into `postgresql_parameters`.  |
| `postgresql_parameters_dcs`                | `postgresql_parameters` merged with `postgresql_parameters_overrides`                                                                                                                                     | Final cluster-wide PostgreSQL parameters used for DCS writes.                |
| `local_postgresql_parameters`              | [...]                                                                                                                                                                                                    | Host-local parameters merged under postgresql.parameters.                    |
| `postgresql_pg_hba`                        | [...]                                                                                                                                                                                                    | Lines rendered into pg_hba.conf template.                                    |
| `postgresql_local_replication_auth_method` | `trust`                                                                                                                                                                                                  | Authentication method for local replication connections.                     |
| `postgresql_pg_ident`                      | `[]`                                                                                                                                                                                                     | Entries rendered into pg_ident.conf via template.                            |
| `postgresql_restore_command`               | pgBackRest/WAL-G command when enabled, otherwise `""`                                                                                                                                                     | If set, added under postgresql.recovery_conf.                                |

`postgresql_parameters_dcs` is the final DCS parameter list. It merges `postgresql_parameters_overrides` into `postgresql_parameters`; if both lists contain the same `option`, the value from `postgresql_parameters_overrides` wins.

`postgresql_locale_provider` sets the default locale provider of a new cluster (initdb, bootstrap only; existing clusters are not changed). initdb has the `--locale-provider` option since PostgreSQL 15 (`libc`, `icu`); `builtin` requires PostgreSQL 17+ (`PG_UNICODE_FAST` requires 18+), and the `C.UTF-8` and `PG_UNICODE_FAST` builtin locales require `postgresql_encoding: UTF8`. `icu` requires `postgresql_icu_locale` (quote values such as `"no"` in YAML) and an encoding that ICU supports (not `SQL_ASCII`, for example). The `pre_checks` role validates these combinations. `postgresql_locale` is still passed to initdb and sets `lc_collate`, `lc_ctype` and the other `lc_*` settings, so it must exist on the hosts.

## Dependencies

This role depends on:

- `vitabaks.autobase.common` - Provides common variables and configurations
- `vitabaks.autobase.bind_address` - Detects the available private IPv4 address
