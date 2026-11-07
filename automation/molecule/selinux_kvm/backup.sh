#!/usr/bin/env bash
# Run on the leader: archive WAL and take a full backup with the variant's backup tool.
#
# Usage: backup.sh <variant: default|consul>
set -euo pipefail

# Test-only: log a "granted" record whenever the backup tool creates a file in its storage,
# so verify.sh can prove the tool ran in its own domain and not in its caller's.
case "$1" in
  default) rule="(auditallow pgbackrest_t pgbackrest_var_lib_t (file (create)))" ;;
  consul) rule="(auditallow walg_t postgresql_db_t (file (create)))" ;;
esac
echo "$rule" >/tmp/test_audit_backup.cil
semodule -i /tmp/test_audit_backup.cil

case "$1" in
  default)
    sudo -u postgres pgbackrest --stanza=postgres-cluster check
    systemd-run --wait --pipe --quiet -p User=postgres pgbackrest --stanza=postgres-cluster --type=full backup
    ;;
  consul)
    # WAL-G file storage expects its root directory to exist
    sudo -u postgres mkdir -p /var/lib/pgsql/wal-g-storage
    sudo -u postgres psql -Atc "create table if not exists selinux_test (); select pg_switch_wal()"
    systemd-run --wait --pipe --quiet -p User=postgres \
      /usr/local/bin/wal-g --config /var/lib/pgsql/.walg.json backup-push /pgdata/18/main
    sleep 10
    ;;
esac
