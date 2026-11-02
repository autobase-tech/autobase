# Ansible Role: selinux

Configures SELinux on RHEL-based hosts (RHEL, Rocky Linux, AlmaLinux, Oracle Linux, CentOS Stream).

## Description

- Sets the SELinux mode (`enforcing` or `permissive`) when `selinux_state` is set.
- Does nothing on hosts where SELinux is disabled or not available (Debian, Ubuntu).
- Never reboots. Enabling SELinux on a host where it is disabled requires a reboot and a relabel, which is left to the operator.

## Role Variables

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| selinux_state | "" | string | `enforcing`, `permissive`, or empty to leave the current mode unchanged. |
| selinux_policy | targeted | string | SELinux policy name. |

## Tags

- `selinux`
