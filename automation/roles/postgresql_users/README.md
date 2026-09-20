# Ansible Role: postgresql_users

This role manages PostgreSQL database users within a PostgreSQL cluster, providing automated creation and configuration of users with proper role attributes, passwords, and role memberships.

Based on [community.postgresql.postgresql_user](https://docs.ansible.com/ansible/latest/collections/community/postgresql/postgresql_user_module.html) module.

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `postgresql_users` | `[]` | List of users to create with configuration parameters |
| `postgresql_users_password_generation` | `disabled` | Password generation mode: `disabled`, `on_create`, or `always` |

### User Configuration Format

Each user entry supports the following parameters:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `name` | Yes | Username for the PostgreSQL user | `"app_user"` |
| `password` | No | User password (encrypted automatically). An empty value is handled according to `postgresql_users_password_generation`. | `"4eJyGyYoueEYlJQu8bL7CtbVx7cgcc5x"` |
| `flags` | No | Role attributes (comma-separated) | `"CREATEDB,NOSUPERUSER"` |
| `role` | No | Additional role to grant to user | `"pg_read_all_data"` |

### Common Role Attributes

| Flag | Description |
|------|-------------|
| `LOGIN` | User can log in (default) |
| `NOLOGIN` | User cannot log in |  
| `CREATEDB` | User can create databases |
| `CREATEROLE` | User can create other users |
| `SUPERUSER` | User has superuser privileges |
| `REPLICATION` | User can perform replication |

### Example:

```yaml
postgresql_users:
  - { name: "app_user", password: "app_user_pass", flags: "LOGIN" }
  - { name: "pgwatch", password: "pgwatch_pass", flags: "LOGIN", role: "pg_monitor" }
```

The default `disabled` mode preserves the previous behavior and does not generate passwords. Set `postgresql_users_password_generation: on_create` to generate a 32-character password for a new user if `password` is missing, empty, or null. Set it to `always` to generate a new password for every user with an empty password on every run. Password generation is skipped for `NOLOGIN` users and users with `state: absent` in all modes.

When `secrets_provider` and `secrets_export_postgresql_users` are enabled, generated passwords are exported by the `secrets` role after users are created or updated. In `on_create` mode, subsequent runs do not change existing passwords or overwrite their exported secrets. Use `always` for intentional rotation, then return the setting to `on_create` to avoid rotating passwords on every run. A non-empty password always takes precedence over generation.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
