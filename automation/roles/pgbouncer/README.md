# Ansible Role: pgbouncer

This role installs and configures [PgBouncer](https://www.pgbouncer.org/), a lightweight connection pooler for PostgreSQL that reduces resource consumption by pooling and reusing database connections.

## Role Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_install` | `true` | Enable or disable PgBouncer installation and configuration |
| `pgbouncer_listen_addr` | `"0.0.0.0"` | IP address for PgBouncer to bind to |
| `pgbouncer_listen_port` | `6432` | Port for PgBouncer to listen on |
| `pgbouncer_processes` | `1` | Number of PgBouncer processes (uses SO_REUSEPORT for multiple) |
| `pgbouncer_conf_dir` | `"/etc/pgbouncer"` | PgBouncer configuration directory |
| `pgbouncer_log_dir` | `"/var/log/pgbouncer"` | PgBouncer log directory |

### Connection Management

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_max_client_conn` | `100000` | Maximum number of client connections |
| `pgbouncer_max_db_connections` | `10000` | Maximum number of database connections |
| `pgbouncer_default_pool_size` | `100` | Default pool size per database |
| `pgbouncer_default_pool_mode` | `"session"` | Default pooling mode (`session`, `transaction`) |
| `pgbouncer_query_wait_timeout` | `120` | Maximum time queries are allowed to spend waiting for execution |
| `pgbouncer_max_prepared_statements` | `1024` | Maximum number of prepared statements per connection |

### Authentication Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_auth_type` | `"{{ postgresql_password_encryption_algorithm }}"` | Authentication method (commonly `scram-sha-256` or `md5`) |
| `pgbouncer_auth_user` | `true` | Use auth_user function for authentication |
| `pgbouncer_auth_username` | `"pgbouncer"` | Username for auth_user queries |
| `pgbouncer_auth_password` | `""` | Optional password for auth_user; an empty value preserves the existing password |
| `pgbouncer_auth_dbname` | `"postgres"` | Database name for auth_user queries |
| `pgbouncer_admin_users` | `"{{ patroni_superuser_username }}"` | Comma-separated list of admin users |
| `pgbouncer_stats_users` | `"{{ patroni_superuser_username }}"` | Comma-separated list of users who can view statistics |

### Advanced Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_ignore_startup_parameters` | `"extra_float_digits,geqo,search_path"` | Comma-separated list of parameters to ignore |

### TLS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_tls_dir` | `"{{ tls_dir }}"` | TLS certificate directory |
| `pgbouncer_client_tls_sslmode` | `"{{ 'require' if tls_cert_generate else 'disable' }}"` | Client TLS mode |
| `pgbouncer_client_tls_key_file` | `"{{ tls_privatekey }}"` | Client TLS private key file |
| `pgbouncer_client_tls_cert_file` | `"{{ tls_cert }}"` | Client TLS certificate file |
| `pgbouncer_client_tls_ca_file` | `"{{ tls_ca_cert }}"` | Client TLS CA certificate file |
| `pgbouncer_client_tls_protocols` | `"secure"` | Client TLS protocols (tlsv1.2, tlsv1.3) |
| `pgbouncer_client_tls_ciphers` | `"secure"` | Client TLS cipher suites |
| `pgbouncer_server_tls_sslmode` | `"{{ 'require' if tls_cert_generate else 'disable' }}"` | Server TLS mode |
| `pgbouncer_server_tls_key_file` | `"{{ tls_privatekey }}"` | Server TLS private key file |
| `pgbouncer_server_tls_cert_file` | `"{{ tls_cert }}"` | Server TLS certificate file |
| `pgbouncer_server_tls_ca_file` | `"{{ tls_ca_cert }}"` | Server TLS CA certificate file |
| `pgbouncer_server_tls_protocols` | `"secure"` | Server TLS protocols (tlsv1.2, tlsv1.3) |
| `pgbouncer_server_tls_ciphers` | `"secure"` | Server TLS cipher suites |

### Pool Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `pgbouncer_pools` | `[]` | List of database pool configurations. |

pgbouncer_pools item fields:
| Field | Description | Example |
|-------|-------------|---------|
| `name` | Pool name | `"postgres"` |
| `dbname` | Target database name | `"postgres"` |
| `pool_parameters` | Optional per-pool parameters | `"pool_size=20 pool_mode=transaction"` |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
