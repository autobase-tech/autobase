# Ansible Role: haproxy

This role installs and configures [HAProxy](http://www.haproxy.org/), a reliable, high-performance TCP/HTTP load balancer that provides load balancing for PostgreSQL database connections.

## Role Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `with_haproxy_load_balancing` | `false` | Enable HAProxy installation and configuration |

### Port Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_listen_port.master` | `5000` | Port for primary database connections |
| `haproxy_listen_port.replicas` | `5001` | Port for read-only replica connections |
| `haproxy_listen_port.replicas_sync` | `5002` | Port for synchronous replica connections |
| `haproxy_listen_port.replicas_async` | `5003` | Port for asynchronous replica connections |
| `haproxy_listen_port.stats` | `7000` | Port for statistics dashboard |
| `haproxy_listen_port.master_direct` |  | Direct primary connections (bypasses PgBouncer) |
| `haproxy_listen_port.replicas_direct` |  | Direct replica connections (bypasses PgBouncer) |
| `haproxy_listen_port.replicas_sync_direct` |  | Direct sync replica connections (bypasses PgBouncer) |
| `haproxy_listen_port.replicas_async_direct` |  | Direct async replica connections (bypasses PgBouncer) |

Note:
- `master_direct`/`replicas_direct`/`replicas_sync_direct`/`replicas_async_direct` are optional and only used when defined (intended to bypass PgBouncer for direct PostgreSQL connections).

### Replica Listeners

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_replicas_sync_enabled` | `true` | Render the `replicas_sync` listener (and `replicas_sync_direct`, if defined) |
| `haproxy_replicas_async_enabled` | `true` | Render the `replicas_async` listener (and `replicas_async_direct`, if defined) |

Set a flag to `false` to disable the listener, for example in a cluster with a single replica, where one of the two would be permanently DOWN.

### Addressing

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_bind_address` | `"{{ bind_address }}"` | Address to bind listeners (stats and data ports) when no VIP is used. |
| `cluster_vip` | `""` | Virtual IP for HAProxy high availability and single entry point; when set, data ports bind to `cluster_vip` while stats bind to `haproxy_bind_address`. |

### Connection Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_maxconn.global` | `100000` | Global HAProxy connection limit |
| `haproxy_maxconn.master` | `10000` | Per-master backend connection limit |
| `haproxy_maxconn.replica` | `10000` | Per-replica backend connection limit |

### Timeout Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_timeout.client` | `"60m"` | Client connection timeout |
| `haproxy_timeout.server` | `"60m"` | Server connection timeout |

### Health Check / Failover Tuning

These map to the `default-server` directive applied to every backend.

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_default_server.inter` | `"3s"` | Interval between health checks |
| `haproxy_default_server.fastinter` | `"1s"` | Check interval while a server is in transition (up↔down) |
| `haproxy_default_server.fall` | `3` | Failed checks before a server is marked down |
| `haproxy_default_server.rise_master` | `4` | Successful checks before the master backend is marked up |
| `haproxy_default_server.rise_replica` | `2` | Successful checks before a replica backend is marked up |
| `haproxy_default_server.on_marked_down` | `"shutdown-sessions"` | Action when a server is marked down. The default terminates in-flight sessions on failover. Set to `""` to **keep active sessions alive** (e.g. preserve long-running queries) when a replica is marked down. |

### Advanced Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `haproxy_log_format` | `""` | Custom log format (JSON structured logging available) |

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
