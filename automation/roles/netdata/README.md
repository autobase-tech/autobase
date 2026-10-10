# Ansible Role: netdata

Installs and configures [Netdata](https://github.com/netdata/netdata) using the official kickstart script.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| netdata_install | true | Enable Netdata installation and configuration. |
| netdata_kickstart_url | `https://get.netdata.cloud/kickstart.sh` | URL to the Netdata kickstart installer script. |
| netdata_install_options | --stable-channel --disable-telemetry --dont-wait | Extra options passed to [kickstart.sh](https://learn.netdata.cloud/docs/netdata-agent/installation/linux/). |
| netdata_install_ignore_errors | true | Continue playbook even if Netdata installation/config fails. |
| netdata_pgbouncer_collector | `{{ pgbouncer_install }}` | Configure the PgBouncer collector when `pgbouncer_install` is enabled. |
| netdata_pgbouncer_stats_user | `{{ patroni_superuser_username }}` | Existing database user used to collect PgBouncer statistics. Automatically added to PgBouncer's `stats_users`. |
| netdata_pgbouncer_stats_password | `{{ patroni_superuser_password }}` | Password for the PgBouncer statistics user. |
| netdata_conf.web_default_port | "19999" | Port for the Netdata web UI. |
| netdata_conf.web_bind_to | "*" | Address to bind the Netdata web server. |
| netdata_conf.db_mode | "dbengine" | Storage mode: dbengine, ram, none. |
| netdata_conf.dbengine_page_cache_size | "64MiB" | In-memory page cache size. |
| netdata_conf.dbengine_tier_0_retention_size | "1024MiB" | Tier 0 retention size (per-second data). |
| netdata_conf.dbengine_tier_0_retention_time | "14d" | Tier 0 retention time. |
| netdata_conf.dbengine_tier_1_retention_size | "1024MiB" | Tier 1 retention size (per-minute data). |
| netdata_conf.dbengine_tier_1_retention_time | "3mo" | Tier 1 retention time. |
| netdata_conf.dbengine_tier_2_retention_size | "1024MiB" | Tier 2 retention size (per-hour data). |
| netdata_conf.dbengine_tier_2_retention_time | "1y" | Tier 2 retention time. |

## PgBouncer monitoring

When both Netdata and PgBouncer are enabled, the role writes `/etc/netdata/go.d/pgbouncer.conf` and notifies a handler to restart Netdata when the configuration changes. Each PgBouncer process gets a separate job (`pgbouncer`, `pgbouncer-2`, etc.) connected through its Unix socket using `pgbouncer_listen_port`. Unix socket connections also work when PgBouncer requires TLS for TCP clients.

The default credentials belong to the existing Patroni superuser. To use a dedicated account with read-only access to the PgBouncer console, create a PostgreSQL login through `postgresql_users` and set `netdata_pgbouncer_stats_user` and `netdata_pgbouncer_stats_password` to its credentials. With `pgbouncer_auth_user: false`, the normal PgBouncer configuration step includes that account in `userlist.txt`.

The collector configuration is owned by `root:netdata` with mode `0640`, and its contents are hidden from Ansible logs. Setting `netdata_pgbouncer_collector: false` or `pgbouncer_install: false` removes the configuration when the Netdata role runs.

Use `--tags pgbouncer,netdata_pgbouncer` with `deploy_pgcluster.yml` or `config_pgcluster.yml` to update PgBouncer and its collector jobs together. The `netdata_pgbouncer` tag only manages the collector configuration; installation and general Netdata configuration use the `netdata` tag. The restart handler runs once after configuration changes.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
