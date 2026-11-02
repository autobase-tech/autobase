# Ansible Role: wal_g

This role installs and configures [WAL-G](https://github.com/wal-g/wal-g), an archival and restoration tool for PostgreSQL. WAL-G is designed to perform continuous archiving of PostgreSQL WAL files and provide point-in-time recovery capabilities with cloud storage support.

## Variables

| Variable | Default | Description |
|---|---|---|
| wal_g_install | false | Master toggle to install/configure WAL-G. |
| wal_g_installation_method | "binary" | Installation path: "binary" or "src". Builds from source on RHEL8 automatically due to GLIBC constraints. |
| wal_g_version | 3.0.7 | WAL-G version. |
| wal_g_path | `/usr/local/bin/wal-g --config {{ postgresql_home_dir }}/.walg.json` | WAL-G executable plus default config argument. The binary is copied to the first path segment. |
| wal_g_json | [...] | WAL-G configuration variables (option:value). |
| wal_g_archive_command | `{{ wal_g_path }} wal-push %p` | archive_command used by PostgreSQL. |
| wal_g_restore_command | `{{ wal_g_path }} wal-fetch %f %p` | restore_command used by PostgreSQL. |
| wal_g_restore_backup_name | `LATEST` | Backup name passed to `backup-fetch`. Set a name from `wal-g backup-list` to restore a specific backup. |
| wal_g_restore_target_time | `""` | Optional PITR target time, for example `"2026-06-26 11:00:00+00"`. |
| wal_g_restore_immediate | `false` | Set to `true` to stop recovery as soon as the restored backup becomes consistent. A non-empty `wal_g_restore_target_time` takes precedence. |
| wal_g_restore_target_action | `{{ restore_target_action \| default('promote') }}` | Action after reaching the target: pause, promote, or shutdown. |
| wal_g_restore_target_timeline | `{{ restore_target_timeline \| default('latest') }}` | Timeline to recover along: current, latest, or a timeline ID. |
| wal_g_patroni_cluster_bootstrap_command | `{{ wal_g_path }} backup-fetch {{ postgresql_data_dir }} {{ wal_g_restore_backup_name }}` | Patroni bootstrap command for recovery from a WAL-G backup. |
| wal_g_patroni_cluster_bootstrap_recovery_conf | [...] | Recovery parameters generated from `wal_g_restore_target_time` or `wal_g_restore_immediate`. |
| wal_g_backup_command | [...] | Parts that form the backup command (joined into a single string for cron). |
| wal_g_delete_command | [...] | Parts that form the retention delete command (joined into a single string for cron). |
| wal_g_cron_jobs | [...] | List of cron jobs. Each item supports: name, user, file, minute, hour, day, month, weekday, job, state, disabled. |
| wal_g_prefetch_dir_create | true | Create WAL-G prefetch directory. |
| wal_g_prefetch_dir_path | `{{ postgresql_home_dir }}/wal-g-prefetch` | Prefetch directory path. |

Notes:
- Binary installation is skipped if the installed version equals wal_g_version.
- On RHEL 8, the role builds from source due to GLIBC requirements for official binaries.
- The role creates ~postgres/.walg.json and the prefetch directory when enabled.
- Cron jobs are created via ansible.builtin.cron from wal_g_cron_jobs.

### WAL-G auto conf (cloud_backup_provider)

If `cloud_backup_provider` (or its default, `cloud_provider`) is set, the role runs tasks/[auto_conf.yml](./tasks/auto_conf.yml) to automatically build WAL-G config.

Set a persistent `cloud_backup_storage_id` in `group_vars/all.yml` or inventory `all.vars` to use the same deterministic backup storage names
as `cloud_resources`, including during standalone configuration runs. Explicit WAL-G prefixes and account settings take precedence over provider names,
which take precedence over generated names. Without an ID, the previous naming behavior is preserved.
See [Backup storage names](../cloud_resources/README.md#backup-storage-names) before enabling this for an existing cluster.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
