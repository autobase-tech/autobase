# Ansible Role: add_repository

This role manages repository configuration for PostgreSQL and other packages. It handles the installation and configuration of various repositories including PostgreSQL PGDG repository, EPEL repository, and extension repositories like TimescaleDB and Citus.

## Description

The `add_repository` role is responsible for:

- Adding custom repositories on Debian/Ubuntu systems using `deb822_repository`
- Adding custom repositories on RedHat/CentOS systems using `yum_repository`
- Installing and configuring PostgreSQL PGDG repository
- Enabling PostgreSQL extras repository for additional packages
- Installing EPEL repository for extra packages
- Enabling PowerTools and CodeReady Builder repositories
- Setting up extension repositories (TimescaleDB, Citus)
- Managing debuginfo repositories for debugging purposes

## Variables

### Repository Control Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `postgresql_distribution` | `community` | `community` (PGDG repository) or `percona` (Percona Distribution for PostgreSQL, enabled with `percona-release setup ppg-<postgresql_version>`) |
| `install_postgresql_repo` | `true` | Install the PostgreSQL repository: PGDG (pgdg-redhat-repo-latest.noarch.rpm) or Percona (`percona-release` package) |
| `install_postgresql_repo_extras` | `true` | Enable PostgreSQL extras repository (e.g., pgdg-rhel8-extras) for additional packages like HAProxy |
| `install_epel_repo` | `true` | Install EPEL repository from epel-release-latest.noarch.rpm |

### Repository Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `apt_repository` | `[]` | List of APT repositories for Debian/Ubuntu systems |
| `yum_repository` | `[]` | List of YUM repositories for RedHat/CentOS systems |
| `proxy_env` | `{}` | Proxy environment variables |

### Extension Control Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `enable_timescale` / `enable_timescaledb` | `false` | Enable TimescaleDB repository |
| `enable_citus` | `false` | Enable Citus repository |

## Repository Definitions

### APT Repository Format

```yaml
apt_repository:
  - name: "repository-name"              # Optional, auto-generated from URI if not specified
    types: ["deb"]                       # Repository types (default: ["deb"])
    uris: "https://example.com/repo"     # Repository URI
    signed_by: "https://example.com/key" # GPG key URL or path
    suites: "focal"                      # Distribution suite
    components: ["main"]                 # Repository components
    enabled: true                        # Whether repository is enabled (default: true)
```

### YUM Repository Format

```yaml
yum_repository:
  - name: "repository-name"
    description: "Repository Description"
    baseurl: "https://example.com/repo"
    gpgkey: "https://example.com/key"    # Optional
    gpgcheck: true                       # Optional (default: true)
    enabled: true                        # Optional (default: true)
```

## Dependencies

This role depends on:
- `vitabaks.autobase.common` - Provides common variables and configurations
