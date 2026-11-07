# Ansible Role: pre_checks

Pre-deployment validations and safety checks for the PostgreSQL cluster stack.

### What it does
- Verifies Ansible version and supported OS/distribution/version.
- System checks/tuning:
  - Ensures systemd RemoveIPC is disabled (avoids PostgreSQL shared memory errors).
  - Disables unattended-upgrades on Debian-based systems (prevents automatic Patroni restarts).
  - HugePages: estimates vm.nr_hugepages for large shared_buffers (>= 8GB) and optionally sets it.
- Patroni:
  - Validates data directory state depending on cluster stage.
- Locale provider:
  - Validates `postgresql_locale_provider`, `postgresql_icu_locale` and `postgresql_builtin_locale` against the PostgreSQL version and encoding before initdb runs.
- PgBouncer:
  - Computes total pool size and ensures it does not exceed max_connections.
- PgDog:
  - Ensures it is not combined with PgBouncer or HAProxy.
  - Validates the architecture and the glibc version required by the PgDog binaries.
  - Validates the authentication settings and `pgdog_pools`.
  - Computes total pool size for all the nodes and ensures it does not exceed max_connections.
- Backup tools:
  - Ensures archive_command for pgBackRest or WAL-G.
  - Validates pgBackRest repo host/user when using a dedicated repo server.
- Extensions:
  - Adds required shared_preload_libraries.
  - Validates versions/OS for TimescaleDB, pgvectorscale, ParadeDB, etc.
- Credentials:
  - Generates Patroni passwords (and the PgDog admin password) when missing or fetches existing ones during maintenance.
- External secrets:
  - Validates the provider, secret definitions, AWS region, recovery window, and tags before cluster changes begin.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
