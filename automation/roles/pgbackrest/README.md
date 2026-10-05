# Ansible Role: pgbackrest

Installs and configures [pgBackRest](https://github.com/pgbackrest/pgbackrest) for PostgreSQL backups and restores. Supports local and cloud repositories, optional dedicated repo host, Patroni bootstrap from backup, and cron-based scheduling.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| `pgbackrest_install` | `false` | Enable installation and configuration of pgBackRest. |
| `pgbackrest_install_from_pgdg_repo` | `true` | Install packages from PGDG repositories. |
| `pgbackrest_stanza` | `"{{ patroni_cluster_name }}"` | Stanza name used by pgBackRest. |
| `pgbackrest_repo_type` | `"posix"` | Repository type: posix, s3, gcs, azure. |
| `pgbackrest_repo_shared` | `false` | Set to `true` if a posix repo is on a shared network filesystem: stanza-create runs only on the master. |
| `pgbackrest_repo_host` | `""` | Dedicated repository host (optional). |
| `pgbackrest_repo_user` | `"postgres"` | SSH user on repo_host (when repo_host is set). |
| `pgbackrest_db_user` | `""` | PostgreSQL user for pgBackRest connections. If empty, uses the OS user or `PGUSER` (normally `postgres`). |
| `pgbackrest_conf_file` | `"/etc/pgbackrest/pgbackrest.conf"` | Path to pgBackRest config file on DB hosts. |
| `pgbackrest_conf.global` | [...] | List of global options (section [global]); see defaults. |
| `pgbackrest_conf.stanza` | [...] | List of stanza options (section [stanza]); see defaults. |
| `pgbackrest_server_conf.global` | [...] | Global options for a dedicated repo server (generated when repo_host is set). |
| `pgbackrest_server_conf.stanza` | `[]` | Stanza options for a dedicated repo server (written to `conf.d/<stanza>.conf`). Database connection options (`pgX-*`) are generated automatically unless overridden by custom options. |
| `pgbackrest_archive_command` | `"pgbackrest --stanza={{ pgbackrest_stanza }} archive-push %p"` | WAL archive_command helper string. |
| `pgbackrest_restore_command` | `"pgbackrest --stanza={{ pgbackrest_stanza }} archive-get %f %p"` | WAL restore_command helper string. |
| `pgbackrest_restore_target_time` | `""` | Optional PITR target time, for example `"2020-06-01 11:00:00+03"`. Adds `--type=time --target=...` to the cluster restore command. |
| `pgbackrest_restore_immediate` | `false` | Set to `true` to add `--type=immediate`. A non-empty `pgbackrest_restore_target_time` takes precedence. |
| `pgbackrest_restore_target_action` | `{{ restore_target_action \| default('promote') }}` | Action after reaching the target: pause, promote, or shutdown. Added to the pgBackRest command only when targeted recovery is configured. |
| `pgbackrest_restore_target_timeline` | `{{ restore_target_timeline \| default('latest') }}` | Timeline to recover along: current, latest, or a timeline ID. Not passed to pgBackRest for immediate recovery. |
| `pgbackrest_restore_backup_name` | `""` | Optional backup set name added as `--set=...`. An empty value lets pgBackRest restore the latest backup set. |
| `pgbackrest_patroni_cluster_restore_command` | `"/usr/bin/pgbackrest --stanza={{ pgbackrest_stanza }} --type=default --delta restore"` | Base restore command. Includes the configured backup set and recovery type. |
| `pgbackrest_patroni_cluster_bootstrap_command` | Derived | Cluster bootstrap/master command with target action and timeline options. |
| `pgbackrest_patroni_replica_restore_command` | Derived | Replica restore command. Uses pause only at a configured PITR target and applies the selected timeline. |
| `pgbackrest_patroni_cluster_bootstrap_recovery_conf` | [...] | List for Patroni recovery parameters (restore_command, recovery_target_action, etc.). |
| `pgbackrest_patroni_cluster_clean_bootstrap` | `false` | Controls how Patroni bootstraps from a pgBackRest backup: false – delta restore into the existing data directory (faster, reuses unchanged files). true – clean restore into an empty data directory (wipes existing contents first). |
| `pgbackrest_cron_jobs` | [...] | Cron jobs for backups (full/diff). Created on DB host by default, or on repo_host if defined. |

Note: To bootstrap via backup set `patroni_cluster_bootstrap_method: "pgbackrest"`.

### pgBackRest Configuration Structure

The `pgbackrest_conf` variable uses a dictionary with global and stanza sections:
- `global`: repository and general settings
- `stanza`: database-specific settings (`pg1-path`, `pg1-socket-path`, etc.)

When a dedicated backup server is used (`pgbackrest_repo_host` is defined), `pgbackrest_server_conf` is used on the repository host:
- `global`: repository and general settings written to `/etc/pgbackrest/pgbackrest.conf`
- `stanza`: custom options for the stanza configuration in `/etc/pgbackrest/conf.d/<stanza>.conf`. Database connection options (`pg1-*`, `pg2-*`, ...) are added automatically, but any explicitly defined custom values take precedence over auto-generated ones.

### Database User for Backups (Least Privilege)

Unless `pg-user` is explicitly configured, pgBackRest connects to PostgreSQL using the local OS user or `PGUSER` (normally `postgres`). You can specify a dedicated user for pgBackRest with restricted privileges by setting `pgbackrest_db_user`:

```yaml
pgbackrest_db_user: "pgbackrest"
```

When set:
- pgBackRest stanza configurations on both the repository server (`conf.d/<stanza>.conf`) and database nodes (`pgbackrest.conf`) will include `pgX-user={{ pgbackrest_db_user }}`.
- The user must be created, granted access in `postgresql_pg_hba`, and given appropriate backup privileges:

```yaml
pgbackrest_db_user: "pgbackrest"

# 1. Allow local socket access to the 'postgres' database in pg_hba.conf (must precede 'local all all')
postgresql_pg_hba:
  - { type: "local", database: "all", user: "{{ patroni_superuser_username }}", address: "", method: "trust" }
  - { type: "local", database: "all", user: "{{ pgbouncer_auth_username }}", address: "", method: "trust" }
  - { type: "local", database: "postgres", user: "pgbackrest", address: "", method: "trust" }
  - { type: "local", database: "all", user: "all", address: "", method: "{{ postgresql_password_encryption_algorithm }}" }
  # ...

# 2. Create the database user with least-privilege roles
postgresql_users:
  - name: "pgbackrest"
    flags: "LOGIN"
    role: "pg_checkpoint,pg_read_all_settings,pg_read_all_stats"

# 3. Grant execution privileges on backup functions in pg_catalog
postgresql_privs:
  - role: "pgbackrest"
    privs: "EXECUTE"
    type: "function"
    db: "postgres"
    objs: "pg_backup_start(text:boolean),pg_backup_stop(boolean),pg_switch_wal(),pg_create_restore_point(text)"
    schema: "pg_catalog"
```


### pgBackRest auto conf (cloud_backup_provider)

If `cloud_backup_provider` (or its default, `cloud_provider`) is set, the role runs tasks/[auto_conf.yml](./tasks/auto_conf.yml) to automatically build `pgbackrest_conf` for the selected backend.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
