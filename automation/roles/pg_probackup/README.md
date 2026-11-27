# Ansible Role: pg_probackup

Installs pg_probackup from the official PostgresPro repository and exposes variables for restore/bootstrap integration with Patroni.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| pg_probackup_install | false | Enable installation/configuration of pg_probackup. |
| pg_probackup_install_from_postgrespro_repo | true | Install from PostgresPro repositories (apt/yum). |
| pg_probackup_version | "`{{ postgresql_version }}`" | pg_probackup major version to install (matches PostgreSQL major by default). |
| pg_probackup_instance | `patroni_scope` | Instance name used to select backups during restore. |
| pg_probackup_dir | "/mnt/backup_dir" | Repository base directory used by pg_probackup. |
| pg_probackup_threads | "4" | Number of parallel threads for restore/backup operations. |
| pg_probackup_add_keys | "`--recovery-target=latest --skip-external-dirs --no-validate`" | Extra flags appended to restore command. |
| pg_probackup_command_parts | [`"pg_probackup-{{ pg_probackup_version }}"," restore -B {{ pg_probackup_dir }}"," --instance {{ pg_probackup_instance }}"," -j {{ pg_probackup_threads }}"," {{ pg_probackup_add_keys }}"`] | Command parts used to build restore command. |
| pg_probackup_restore_command | "`{{ pg_probackup_command_parts }}`" | Full restore command string. |
| pg_probackup_patroni_cluster_bootstrap_command | "`{{ pg_probackup_command_parts }}`" | Command used by Patroni bootstrap method "pg_probackup". |

Note: To bootstrap a cluster from pg_probackup with Patroni, set `patroni_cluster_bootstrap_method: "pg_probackup"`.

For an existing unsharded backup repository, set `pg_probackup_instance` explicitly if the registered instance uses a different name.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
