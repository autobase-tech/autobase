# Autobase Platform

**Autobase Platform** is a comprehensive solution for managing the lifecycle of PostgreSQL clusters. The project consists of two main parts:

- **Console** — a web application (UI, API, DB) for cluster management, monitoring, and operations.
- **Automation** — an automation system based on Ansible (playbooks and roles) for deploying, upgrading, and maintaining PostgreSQL clusters.

Console and Automation are tightly integrated: users interact via the UI, which sends commands to the API. The API, when necessary, triggers Ansible playbooks to automate cluster operations.

## Console Stack

The Console stack includes the following core components:

- **Console UI**: A web interface for managing clusters, launching operations, and monitoring status.
- **Console API**: A REST API that receives requests from the UI, reads from and writes to the database, and starts the Automation container when required.
- **Console DB**: A PostgreSQL database that stores cluster configurations, server details, settings, and operation results.

### Architecture

```
             +---------------------- Autobase Platform ----------------------+
+------+     | +------------+    +-------------+    +----------------------+ |     +---------------------+
| User | --> | | Console UI | -> | Console API | -> | Automation (Ansible) | | --> | PostgreSQL Clusters |
+------+     | +------------+    +-------------+    +----------------------+ |     |        1..N         |
             |                           v                                   |     +---------------------+
             |                    +------------+                             |
             |                    | Console DB |                             |
             |                    +------------+                             |
             +---------------------------------------------------------------+
```

For a detailed description of the cluster components, visit the [Architecture page](https://autobase.tech/docs/overview/architecture).

## Quick Start

> [!NOTE]
> Run Autobase Platform in the same network as the target database servers so that it can deploy clusters and collect status information.

### Docker Compose

1. Clone the repository:

   ```sh
   git clone https://github.com/autobase-tech/autobase.git
   ```

2. Navigate to the `console` directory:

   ```sh
   cd autobase/console
   ```

#### Basic Setup

Use this setup to run Autobase Platform without automatic SSL certificate management.

```sh
docker compose up -d
```

Open `http://autobase-server-ip` and complete the initial setup.

#### Setup with SSL

Use this setup if you have a domain name and want Caddy to obtain and renew SSL certificates automatically.

1. Create a DNS A record that points your domain to the IP address of the server running Autobase Platform.

2. Create a `.env` file with your domain and email address:

   ```sh
   DOMAIN=autobase.your-domain.com
   EMAIL=admin@your-domain.com
   ```

3. Run Docker Compose with Caddy:

   ```sh
   docker compose -f docker-compose.ssl.yml up -d
   ```

Open `https://autobase.your-domain.com` and complete the initial setup.

For more deployment options, see the [Deployment](https://autobase.tech/docs/category/deployment) documentation.

## Notes

- The basic setup exposes the Console UI on port 80 without SSL.
- In the SSL setup, Caddy obtains and renews certificates for your domain automatically.
- Data is persisted in the `console_postgres` and `dbdesk_studio_data` Docker volumes, as well as `caddy_data` when using Caddy.
- Docker Compose creates the required networks automatically.
- All services are configured to restart automatically unless stopped manually.

## Using Docker Secrets

Sensitive values, such as the authorization token and database password, can be supplied through files mounted under `/run/secrets` instead of being stored as plain text in `.env`. The API supports the `_FILE` convention for all `PG_CONSOLE_*` variables, and the UI supports it for `PG_CONSOLE_AUTHORIZATION_TOKEN`. As with the official `postgres` image: if `FOO_FILE` is set, the contents of that file are used as the value of `FOO`. Setting both `FOO` and `FOO_FILE` to non-empty values is an error.

Use the provided `docker-compose.secrets.yml` override:

```sh
mkdir -p ./secrets && chmod 700 ./secrets
printf '%s' 'your-secret-token' > ./secrets/auth_token
printf '%s' 'your-db-password'  > ./secrets/db_password
chmod 600 ./secrets/*

docker compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
# or, with Caddy:
docker compose -f docker-compose.ssl.yml -f docker-compose.secrets.yml up -d
```

For a Docker Swarm deployment, replace the `file:` sources in the override with `external: true` and create the secrets with `docker secret create`.

## Configuration

### Console UI

UI polling intervals use milliseconds. The other durations in the API table use Go duration strings such as `2s`, `5m`, or `8h`.

| Variable                                 | Default     | Description                                                                                |
| ---------------------------------------- | ----------- | ------------------------------------------------------------------------------------------ |
| `PG_CONSOLE_API_URL`                     | `/api/v1`   | Browser-facing API URL. The default uses the UI container's Nginx reverse proxy.           |
| `PG_CONSOLE_API_HOST`                    | `localhost` | API hostname used by Nginx. The supplied Compose files set this to `autobase-console-api`. |
| `PG_CONSOLE_API_PORT`                    | `8080`      | API port used by Nginx.                                                                    |
| `PG_CONSOLE_OPERATIONS_POLLING_INTERVAL` | `5000`      | Operation progress and log polling interval, in milliseconds.                              |
| `PG_CONSOLE_REFRESH_INTERVAL`            | `60000`     | Initial refresh interval in the UI, in milliseconds. Users can change it per page.         |
| `PG_CONSOLE_DBDESK_STUDIO_URL`           | `/dbdesk/`  | Browser-facing URL of the SQL editor.                                                      |
| `PG_CONSOLE_DBDESK_STUDIO_HOST`          | `127.0.0.1` | SQL editor hostname used by Nginx. The supplied Compose files set this to `dbdesk-studio`. |
| `PG_CONSOLE_DBDESK_STUDIO_PORT`          | `9876`      | Internal port on which Nginx serves the SQL editor proxy.                                  |
| `DBDESK_EXPRESS_PORT`                    | `6789`      | Upstream dbdesk-studio application port.                                                   |

The UI refresh setting controls browser requests; cluster status updates are collected by the API according to `PG_CONSOLE_CLUSTERWATCHER_RUNEVERY`.

### Console API

| Variable                             | Default                           | Description                                                                       |
| ------------------------------------ | --------------------------------- | --------------------------------------------------------------------------------- |
| `PG_CONSOLE_LOGGER_LEVEL`            | `INFO`                            | Log level. Accepted values: [TRACE, DEBUG, INFO, WARN, ERROR, FATAL, PANIC].      |
| `PG_CONSOLE_HTTP_HOST`               | `0.0.0.0`                         | HTTP listening address. `0.0.0.0` accepts connections on all interfaces.          |
| `PG_CONSOLE_HTTP_PORT`               | `8080`                            | HTTP listening port inside the API container.                                     |
| `PG_CONSOLE_HTTP_WRITETIMEOUT`       | `10s`                             | Maximum HTTP response write duration. Set to `0` to disable.                      |
| `PG_CONSOLE_HTTP_READTIMEOUT`        | `10s`                             | Maximum HTTP request read duration.                                               |
| `PG_CONSOLE_HTTPS_ISUSED`            | `false`                           | Enable the API's own HTTPS listener. Not needed when Caddy terminates HTTPS.      |
| `PG_CONSOLE_HTTPS_HOST`              | `0.0.0.0`                         | HTTPS listening address.                                                          |
| `PG_CONSOLE_HTTPS_PORT`              | `8081`                            | HTTPS listening port inside the API container.                                    |
| `PG_CONSOLE_HTTPS_CACERT`            | `/etc/pg_console/cacert.pem`      | Path to the CA certificate for mutual TLS.                                        |
| `PG_CONSOLE_HTTPS_SERVERCERT`        | `/etc/pg_console/server-cert.pem` | Path to the HTTPS server certificate.                                             |
| `PG_CONSOLE_HTTPS_SERVERKEY`         | `/etc/pg_console/server-key.pem`  | Path to the HTTPS server private key.                                             |
| `PG_CONSOLE_AUTHORIZATION_TOKEN`     | `auth_token`                      | Static bearer token for internal and service API requests.                        |
| `PG_CONSOLE_AUTH_SESSION_TTL`        | `8h`                              | Browser session lifetime.                                                         |
| `PG_CONSOLE_AUTH_COOKIE_SECURE`      | `true`                            | Send session cookies over HTTPS only. The HTTP Compose file sets this to `false`. |
| `PG_CONSOLE_DB_HOST`                 | `localhost`                       | Console database host. The supplied Compose files use `autobase-console-db`.      |
| `PG_CONSOLE_DB_PORT`                 | `5432`                            | Console database port.                                                            |
| `PG_CONSOLE_DB_DBNAME`               | `postgres`                        | Console database name.                                                            |
| `PG_CONSOLE_DB_USER`                 | `postgres`                        | Console database user.                                                            |
| `PG_CONSOLE_DB_PASSWORD`             | `postgres-pass`                   | Console database password. Must match the database container configuration.       |
| `PG_CONSOLE_DB_MAXCONNS`             | `10`                              | Maximum number of database connections in the pool.                               |
| `PG_CONSOLE_DB_MAXCONNLIFETIME`      | `60s`                             | Maximum lifetime of a pooled database connection.                                 |
| `PG_CONSOLE_DB_MAXCONNIDLETIME`      | `60s`                             | Maximum idle time of a pooled database connection.                                |
| `PG_CONSOLE_DB_MIGRATIONDIR`         | `/etc/db/migrations`              | Directory containing database migration scripts inside the API container.         |
| `PG_CONSOLE_ENCRYPTIONKEY`           | `super_secret`                    | Encryption key for stored secrets.                                                |
| `PG_CONSOLE_DOCKER_HOST`             | `unix:///var/run/docker.sock`     | Docker daemon endpoint used to start Automation containers.                       |
| `PG_CONSOLE_DOCKER_LOGDIR`           | `/tmp/ansible`                    | Shared directory for Ansible operation logs. Must match the mounted volume.       |
| `PG_CONSOLE_DOCKER_IMAGE`            | `autobase/automation:2.11.0`      | Automation container image.                                                       |
| `PG_CONSOLE_LOGWATCHER_RUNEVERY`     | `5s`                              | Interval between operation log checks.                                            |
| `PG_CONSOLE_LOGWATCHER_ANALYZEPAST`  | `48h`                             | Age limit for operations considered by the log watcher.                           |
| `PG_CONSOLE_CLUSTERWATCHER_RUNEVERY` | `60s`                             | Interval between cluster status collection runs.                                  |
| `PG_CONSOLE_CLUSTERWATCHER_POOLSIZE` | `4`                               | Number of concurrent cluster watcher requests.                                    |
| `PG_CONSOLE_DBDESK_STUDIO_ENABLED`   | `true`                            | Enable automatic dbdesk-studio registration after successful cluster deploy.      |
| `PG_CONSOLE_DBDESK_STUDIO_API_URL`   | `http://dbdesk-studio:6789`       | dbdesk-studio API base URL.                                                       |
| `PG_CONSOLE_DBDESK_STUDIO_SSLMODE`   | `require`                         | SSL mode for dbdesk-studio postgres connection profiles.                          |
| `PG_CONSOLE_DBDESK_STUDIO_TIMEOUT`   | `5s`                              | HTTP timeout for dbdesk-studio health and registration requests.                  |
| `PG_CONSOLE_MONITORING_HTTP_TIMEOUT` | `2s`                              | Timeout for one Netdata HTTP request.                                             |
| `PG_CONSOLE_MONITORING_NODE_TIMEOUT` | `5s`                              | Monitoring collection timeout per node.                                           |
| `PG_CONSOLE_MONITORING_TIMEOUT`      | `8s`                              | Total monitoring collection timeout, including queued nodes.                      |

Timeouts must satisfy `1ms <= PG_CONSOLE_MONITORING_HTTP_TIMEOUT <= PG_CONSOLE_MONITORING_NODE_TIMEOUT <= PG_CONSOLE_MONITORING_TIMEOUT`. The HTTP write timeout must exceed the total monitoring timeout unless disabled with `0`.

## License

Autobase Platform (Console) is proprietary software. Its use, including under the free Starter plan, is governed by the [Platform license](./LICENSE).

The automation core and the public deployment files and documentation in this repository are licensed under the [MIT License](../LICENSE).
