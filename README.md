<p align="center">
  <img src="images/github-autobase.png">
</p>

# Autobase for PostgreSQL® :elephant: :sparkling_heart:

[![Ansible-lint](https://github.com/autobase-tech/autobase/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/autobase-tech/autobase/actions/workflows/ansible-lint.yml)
[![Yamllint](https://github.com/autobase-tech/autobase/actions/workflows/yamllint.yml/badge.svg)](https://github.com/autobase-tech/autobase/actions/workflows/yamllint.yml)
[![Flake8](https://github.com/autobase-tech/autobase/actions/workflows/flake8.yml/badge.svg)](https://github.com/autobase-tech/autobase/actions/workflows/flake8.yml)
[![Molecule](https://github.com/autobase-tech/autobase/actions/workflows/molecule.yml/badge.svg)](https://github.com/autobase-tech/autobase/actions/workflows/molecule.yml)
[![GitHub license](https://img.shields.io/github/license/autobase-tech/autobase)](https://github.com/autobase-tech/autobase/blob/main/LICENSE)

> This repository contains the open-source automation core, built with Ansible and licensed under the MIT License.

Autobase automates the deployment and management of highly available PostgreSQL clusters in your own infrastructure. It reduces operational costs and makes database management accessible, even for teams without specialized expertise.

**Automate deployment, failover, backup and restore, upgrades, scaling, and more with ease.**

Say goodbye to manual database management 👋

## Documentation

Autobase documentation can be found [here](https://autobase.tech/docs).

## Architecture

![PostgreSQL cluster architecture](images/autobase-postgres.light.png#gh-light-mode-only)
![PostgreSQL cluster architecture](images/autobase-postgres.dark.png#gh-dark-mode-only)

For a detailed description of the cluster components, visit the [Architecture](https://autobase.tech/docs/overview/architecture) page.

## Getting Started

You can deploy PostgreSQL clusters using Autobase Platform (UI), the Ansible Collection, or GitOps.

### Autobase Platform (UI)

- [Autobase Platform](./console/README.md) - an internal database platform for PostgreSQL, bringing the managed database experience of DBaaS into your own infrastructure.

### Ansible Collection

- [Ansible Collection](./automation/README.md) - an Ansible collection for deploying and managing PostgreSQL clusters from the command line.

### GitOps (CI/CD)

- [GitOps](https://autobase.tech/docs/management/gitops) - manage cluster configuration in Git and apply changes through CI/CD pipelines.

> [!TIP]
> 📩 Contact us at info@autobase.tech, and our team will help you integrate Autobase into your infrastructure.

## Compatibility

Autobase supports the following Linux distributions and CPU architectures.

### Supported Linux Distributions

- **Debian**: 11, 12, 13
- **Ubuntu**: 22.04, 24.04, 26.04
- **CentOS Stream**: 9, 10
- **Oracle Linux**: 8, 9, 10
- **Rocky Linux**: 8, 9, 10
- **AlmaLinux**: 8, 9, 10

**CPU architectures:** x86_64 (amd64), aarch64 (arm64).

### PostgreSQL Versions

Supported PostgreSQL major versions: 10, 11, 12, 13, 14, 15, 16, 17, 18.

Available PostgreSQL versions depend on the operating system and package repositories.

### Automated Deployment Tests

The following workflows run daily deployment tests:

| Distribution     |                                                                                                                   Test result                                                                                                                    |
| ---------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| Debian 12        |       [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_debian12.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_debian12.yml)       |
| Debian 13        |       [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_debian13.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_debian13.yml)       |
| Ubuntu 24.04     |     [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_ubuntu2404.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_ubuntu2404.yml)     |
| Ubuntu 26.04     |     [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_ubuntu2604.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_ubuntu2604.yml)     |
| CentOS Stream 9  |  [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_centosstream9.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_centosstream9.yml)  |
| CentOS Stream 10 | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_centosstream10.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_centosstream10.yml) |
| Oracle Linux 9   |  [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_oracle_linux9.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_oracle_linux9.yml)  |
| Oracle Linux 10  | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_oracle_linux10.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_oracle_linux10.yml) |
| Rocky Linux 9    |    [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_rockylinux9.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_rockylinux9.yml)    |
| Rocky Linux 10   |   [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_rockylinux10.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_rockylinux10.yml)   |
| AlmaLinux 9      |     [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_almalinux9.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_almalinux9.yml)     |
| AlmaLinux 10     |    [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/autobase-tech/autobase/schedule_pg_almalinux10.yml?branch=main)](https://github.com/autobase-tech/autobase/actions/workflows/schedule_pg_almalinux10.yml)    |

## Project Status

Autobase has been actively developed since 2019 and is trusted by companies worldwide, including in production environments with high loads and demanding reliability requirements. Our mission is to provide a self-hosted DBaaS that delivers reliability, flexibility, and cost efficiency.

**Autobase is production-ready.**

## Star Us

If you find our project helpful, consider giving it a star on GitHub! Your support helps us grow and motivates us to keep improving. Starring the project is a simple yet effective way to show your appreciation and help others discover it.

<a href="https://www.star-history.com/?type=date&repos=autobase-tech%2Fautobase">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=autobase-tech/autobase&type=date&theme=dark&legend=top-left&sealed_token=VdYxGE_5d92Xolz9F9ZUWnCr8ysiUiSRl4f8Yw6V5AK3RlEU4W1hECTT6IREYWAMxy2KBEvkrrDE7vcLzeqb0WtTRzzDN2QDOQsG5naaj6zq3BXQAVZoEs7Yyiz3HssFq0sjcgeWXj8bvfxCb5WSwTGY8jsc3TN5ZN8wWfRyCNGNmKWsstjDiPM_pmFi" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=autobase-tech/autobase&type=date&legend=top-left&sealed_token=VdYxGE_5d92Xolz9F9ZUWnCr8ysiUiSRl4f8Yw6V5AK3RlEU4W1hECTT6IREYWAMxy2KBEvkrrDE7vcLzeqb0WtTRzzDN2QDOQsG5naaj6zq3BXQAVZoEs7Yyiz3HssFq0sjcgeWXj8bvfxCb5WSwTGY8jsc3TN5ZN8wWfRyCNGNmKWsstjDiPM_pmFi" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=autobase-tech/autobase&type=date&legend=top-left&sealed_token=VdYxGE_5d92Xolz9F9ZUWnCr8ysiUiSRl4f8Yw6V5AK3RlEU4W1hECTT6IREYWAMxy2KBEvkrrDE7vcLzeqb0WtTRzzDN2QDOQsG5naaj6zq3BXQAVZoEs7Yyiz3HssFq0sjcgeWXj8bvfxCb5WSwTGY8jsc3TN5ZN8wWfRyCNGNmKWsstjDiPM_pmFi" />
 </picture>
</a>

## License

Licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Author

Vitaliy Kukharik (PostgreSQL expert, founder of Autobase.tech) \
vitaliy@autobase.tech
