# Ansible Role: postgresql_users

This role manages PostgreSQL database users within a PostgreSQL cluster, providing automated creation and configuration of users with proper role attributes, passwords, and role memberships.

Based on [community.postgresql.postgresql_user](https://docs.ansible.com/ansible/latest/collections/community/postgresql/postgresql_user_module.html) module.

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `postgresql_users` | `[]` | List of users to create with configuration parameters |

### User Configuration Format

Each user entry supports the following parameters:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `name` | Yes | Username for the PostgreSQL user | `"app_user"` |
| `password` | No | User password (encrypted automatically). A password is generated for a new user when this value is empty, unless the user has `NOLOGIN`. | `"4eJyGyYoueEYlJQu8bL7CtbVx7cgcc5x"` |
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

A 32-character password is generated for a new user if `password` is missing, empty, or null. Password generation is skipped for `NOLOGIN` users and users with `state: absent`. When `secrets_provider` and `secrets_export_postgresql_users` are enabled, the generated password is exported by the `secrets` role after the user is created.

On subsequent runs, an empty password does not change the password of an existing user and does not overwrite its exported secret. Set a non-empty password explicitly to rotate it.

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
