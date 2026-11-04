#!/usr/bin/env bash
# Fail unless every PostgreSQL node runs in the expected SELinux mode, every cluster service
# runs in its own domain, the service files are labelled, the services work, and no denial
# was logged for their domains since boot.
#
# Usage: verify.sh <inventory file> <expected mode: Enforcing|Permissive> <variant: default|consul>
set -uo pipefail

INVENTORY="$1"
EXPECTED_MODE="$2"
VARIANT="${3:-default}"
STANZA="${STANZA:-postgres-cluster}"
VIP="192.168.122.200"
SSH=(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)
failures=0

fail() {
  echo "FAIL $1"
  failures=$((failures + 1))
}

# process:domain and path:type expected on every node
PROCESSES="patroni:patroni_t postgres:postgresql_t pgbouncer:pgbouncer_t"
PATHS="/pgdata/18/main:postgresql_db_t /pgwal/18/pg_wal:postgresql_db_t
  /etc/pgbouncer:pgbouncer_etc_t /var/log/pgbouncer:pgbouncer_log_t"
case "$VARIANT" in
  default)
    PROCESSES="$PROCESSES etcd:etcd_t haproxy:haproxy_t confd:confd_t keepalived:keepalived_t"
    PATHS="$PATHS /usr/local/bin/etcd:etcd_exec_t /var/lib/etcd:etcd_var_lib_t
      /var/log/pgbackrest:pgbackrest_log_t /var/lib/pgbackrest:pgbackrest_var_lib_t
      /var/spool/pgbackrest:pgbackrest_spool_t /usr/bin/pgbackrest:pgbackrest_exec_t
      /etc/haproxy/haproxy.cfg:haproxy_conf_t /usr/local/bin/confd:confd_exec_t /etc/confd:confd_etc_t"
    PERMISSIVE_DOMAINS="haproxy_t keepalived_t"
    BACKUP_DOMAIN="pgbackrest_t"
    ;;
  consul)
    PROCESSES="$PROCESSES consul:consul_t vip-manager:vip_manager_t"
    PATHS="$PATHS /etc/consul:consul_etc_t /var/lib/consul:consul_var_lib_t
      /usr/local/bin/wal-g:walg_exec_t /usr/bin/vip-manager:vip_manager_exec_t"
    PERMISSIVE_DOMAINS=""
    BACKUP_DOMAIN="walg_t"
    ;;
  *) echo "unknown variant $VARIANT"; exit 2 ;;
esac
DOMAINS=$(for p in $PROCESSES; do echo "${p#*:}"; done | sort -u | paste -sd'|' -)"|$BACKUP_DOMAIN"

ips=$(awk '/^\[master\]|^\[replica\]/{f=1;next} /^\[/{f=0} f && NF {print $1}' "$INVENTORY")
for ip in $ips; do
  mode=$("${SSH[@]}" "root@$ip" getenforce)
  [ "$mode" = "$EXPECTED_MODE" ] || fail "$ip: SELinux is $mode, expected $EXPECTED_MODE"

  for check in $PROCESSES; do
    comm=${check%%:*}
    domain=${check#*:}
    domains=$("${SSH[@]}" "root@$ip" "ps -C $comm -o label= | cut -d: -f3 | sort -u | tr '\n' ' '")
    [ "$domains" = "$domain " ] || fail "$ip: $comm runs as '${domains:-nothing}', expected $domain"
  done

  for check in $PATHS; do
    path=${check%%:*}
    expected=${check#*:}
    type=$("${SSH[@]}" "root@$ip" "stat -c %C $path | cut -d: -f3")
    [ "$type" = "$expected" ] || fail "$ip: $path is ${type:-missing}, expected $expected"
  done

  for domain in $PERMISSIVE_DOMAINS; do
    "${SSH[@]}" "root@$ip" "semanage permissive -l | grep -qx $domain" && fail "$ip: $domain is a permissive domain"
  done

  # "0 denials" only counts if the audit log is actually being read.
  "${SSH[@]}" "root@$ip" 'ausearch --input-logs -m DAEMON_START -ts boot >/dev/null 2>&1' \
    || fail "$ip: no audit records since boot, is auditd running?"

  # Only the domains of the cluster services count; denials of unrelated system services
  # (sshd, chronyd, ...) are not in scope here.
  denials=$("${SSH[@]}" "root@$ip" "ausearch --input-logs -m AVC,USER_AVC,SELINUX_ERR -ts boot 2>/dev/null \
    | grep -E '^type=(AVC|USER_AVC|SELINUX_ERR)' | grep -v 'avc:  granted' | grep -c -E 'scontext=[^ ]*:($DOMAINS):'")
  [ "${denials:-0}" -eq 0 ] || fail "$ip: $denials SELinux denials for $DOMAINS since boot"

  # A query through PgBouncer (pgbouncer_t -> PostgreSQL socket)
  "${SSH[@]}" "root@$ip" "PGPASSWORD=db1_user-test-pass psql -h 127.0.0.1 -p 6432 -U db1_user -d db1 -Atc 'select 1'" \
    | grep -qx 1 || fail "$ip: no query through PgBouncer"
done

leader=$(bash "$(dirname "$0")/leader.sh" "$INVENTORY")

# The VIP is held by keepalived (default) or vip-manager (consul) on exactly one node
holders=$(for ip in $ips; do "${SSH[@]}" "root@$ip" "ip -o addr show | grep -q ' $VIP/' && echo $ip"; done)
[ "$(echo "$holders" | grep -c .)" -eq 1 ] || fail "VIP $VIP is held by '${holders//$'\n'/ }', expected exactly one node"
if [ "$VARIANT" = consul ] && [ "$holders" != "$leader" ]; then
  fail "VIP $VIP is on $holders, expected the leader $leader (vip-manager)"
fi

# WAL archiving (archive_command in postgresql_t) and a full backup started by systemd
case "$VARIANT" in
  default)
    info=$("${SSH[@]}" "root@$leader" "sudo -u postgres pgbackrest --stanza=$STANZA --output=json info")
    echo "$info" | python3 -c "
import json, sys
stanza = json.load(sys.stdin)[0]
assert stanza['status']['code'] == 0, stanza['status']
assert stanza['backup'], 'no backup'
assert stanza['archive'] and stanza['archive'][0].get('max'), 'no archived WAL'
" || fail "pgBackRest: no successful backup or archived WAL in stanza $STANZA"
    ;;
  consul)
    "${SSH[@]}" "root@$leader" "sudo -u postgres /usr/local/bin/wal-g --config /var/lib/pgsql/.walg.json backup-list" \
      | grep -q base_ || fail "WAL-G: no backup in the storage"
    "${SSH[@]}" "root@$leader" "ls /var/lib/pgsql/wal-g-storage/wal_005 | grep -q ." \
      || fail "WAL-G: no archived WAL in the storage"
    ;;
esac

# The workflow loads an auditallow rule before archiving and backing up; a "granted" record
# shows that the backup tool wrote its storage from its own domain, not from its caller's.
"${SSH[@]}" "root@$leader" "ausearch --input-logs -m AVC -ts boot 2>/dev/null | grep 'avc:  granted' \
  | grep -q 'scontext=[^ ]*:$BACKUP_DOMAIN:'" || fail "the backup tool did not run in $BACKUP_DOMAIN"

[ "$failures" -eq 0 ] && echo "SELinux checks passed" || exit 1
