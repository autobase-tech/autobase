# Ansible Role: packages

This role installs system packages and PostgreSQL packages from repositories (dnf/apt) and optionally perf/FlameGraph and packages from local files.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| installation_method | "packages" | Installation method: "packages" (deb/rpm). |
| system_packages | [...] | List of system packages to install. |
| postgresql_packages | [...] | List of PostgreSQL packages to install. |
| packages_from_file | [] | Optional list of local package files (deb/rpm) to install from /files directory. |
| install_perf | false | Install perf and FlameGraph helper. |
| python_version | "3" | Python major version to select alternatives (RedHat) and package names. |
| skip_dnf_makecache | false | Skip DNF cache refresh on RedHat family. |
| proxy_env | {} | Optional proxy environment for package downloads. |


## Extension Auto-Setup

This role can install popular PostgreSQL extensions automatically when corresponding enable_*** flags are set. It picks the correct package name for Debian/RedHat, handles version mapping where needed, and for some extensions fetches artifacts directly from GitHub (via tasks/extensions_github.yml) using regex-based matching.

| Variable | Default | Description |
|---|---|---|
| enable_timescale / enable_timescaledb | false | Install TimescaleDB package.|
| enable_citus | false | Install Citus package. |
| enable_pg_repack | false | Install pg_repack package. |
| enable_pg_cron | false | Install pg_cron package. |
| enable_pgaudit | false | Install pgaudit package. |
| enable_postgis | false | Install PostGIS package. |
| enable_pgrouting | false | Install pgRouting package. |
| enable_pg_stat_kcache | false | Install pg_stat_kcache package. |
| enable_pg_wait_sampling | false | Install pg_wait_sampling package. |
| enable_pg_partman | false | Install pg_partman package. |
| enable_pgvector | false | Install pgvector package. |
| enable_pg_tde | false | Install Percona pg_tde (Transparent Data Encryption) package and add `pg_tde` to `shared_preload_libraries`. Requires `postgresql_distribution: percona` and PostgreSQL 17+. The `postgresql_extensions` role then creates the extension in `pg_tde_databases` and configures a **local file** key provider and a principal key (`pg_tde_key_file`, `pg_tde_key_provider_name`, `pg_tde_principal_key_name`); the key file is copied to all cluster nodes. The keys are stored unencrypted in that file (development/testing only). |
| enable_pgvectorscale | false | Install pgvectorscale from GitHub releases. |
| enable_pg_search / enable_paradedb | false | Install ParadeDB’s pg_search from GitHub releases. |
| enable_pg_analytics / enable_paradedb | false | Install pg_analytics from GitHub releases. |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
