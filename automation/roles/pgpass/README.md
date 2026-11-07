# Ansible Role: pgpass

Creates and manages the `~/.pgpass` file for the postgres user. The role ensures the target home directory exists, writes entries provided via variables, and enforces secure file permissions (0600).

## Role Variables

| Variable             | Type         | Default                                         | Description |
|----------------------|--------------|-------------------------------------------------|-------------|
| postgresql_pgpass    | list[string] | [...]                                              | Lines to write to ~/.pgpass. If empty/undefined, the role does nothing. Each line must follow hostname:port:database:username:password. |
| postgresql_home_dir  | string       | /var/lib/postgresql (Debian) or /var/lib/pgsql (RedHat) | Home directory where ~/.pgpass is created (owned by postgres). |

### Example

```yaml
postgresql_pgpass:
  - "localhost:{{ postgresql_port }}:*:{{ patroni_superuser_username }}:{{ patroni_superuser_password }}"
  - "{{ bind_address }}:{{ postgresql_port }}:*:{{ patroni_superuser_username }}:{{ patroni_superuser_password }}"
  - "*:{{ connection_pooler_port }}:*:{{ patroni_superuser_username }}:{{ patroni_superuser_password }}"
```


## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations

## PostgreSQL CLI authentication

Set `postgresql_cli_passfile` to configure the automation password file path
(default: `{{ postgresql_home_dir }}/.pgpass_autobase`). Preparing the file with
`tasks_from: automation` saves its path in the host fact
`_postgresql_cli_passfile_path`, which remains available across plays.

After preparation, CLI tasks must use the saved path:

```yaml
environment:
  PGPASSFILE: "{{ _postgresql_cli_passfile_path }}"
```

For delegated tasks, use `hostvars[target_host]._postgresql_cli_passfile_path`.
Install-user commands use `{{ _postgresql_cli_passfile_path }}.upgrade` after
preparing it with `tasks_from: upgrade`.

Using `PGPASSFILE` instead of `PGPASSWORD` keeps authentication passwords out of
command lines and sudo logs without requiring local `trust` authentication.

The file is owned by `postgres` with permissions `0600` and managed separately
from the user's `~/.pgpass` and Patroni's `.pgpass_patroni`.

PgBouncer pause requires the same `postgresql_cli_passfile` path on all database hosts.
