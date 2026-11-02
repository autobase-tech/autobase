#!/usr/bin/env bash
# Fail unless every PostgreSQL node runs in the expected SELinux mode, with Patroni and
# PostgreSQL confined, the data directories labelled and no denials since boot.
#
# Usage: verify.sh <inventory file> <expected mode: Enforcing|Permissive>
set -uo pipefail

INVENTORY="$1"
EXPECTED_MODE="$2"
SSH=(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)
failures=0

fail() {
  echo "FAIL $1"
  failures=$((failures + 1))
}

ips=$(awk '/^\[master\]|^\[replica\]/{f=1;next} /^\[/{f=0} f && NF {print $1}' "$INVENTORY")
for ip in $ips; do
  mode=$("${SSH[@]}" "root@$ip" getenforce)
  [ "$mode" = "$EXPECTED_MODE" ] || fail "$ip: SELinux is $mode, expected $EXPECTED_MODE"

  for check in "patroni:patroni_t" "postgres:postgresql_t"; do
    comm=${check%%:*}
    domain=${check#*:}
    domains=$("${SSH[@]}" "root@$ip" "ps -C $comm -o label= | cut -d: -f3 | sort -u | tr '\n' ' '")
    [ "$domains" = "$domain " ] || fail "$ip: $comm runs as '${domains:-nothing}', expected $domain"
  done

  for path in /pgdata/18/main /pgwal/18/pg_wal; do
    type=$("${SSH[@]}" "root@$ip" "stat -c %C $path | cut -d: -f3")
    [ "$type" = "postgresql_db_t" ] || fail "$ip: $path is $type, expected postgresql_db_t"
  done

  # "0 denials" only counts if the audit log is actually being read.
  "${SSH[@]}" "root@$ip" 'ausearch --input-logs -m DAEMON_START -ts boot >/dev/null 2>&1' \
    || fail "$ip: no audit records since boot, is auditd running?"

  # Only the confined domains count; other services (e.g. haproxy_t, which Autobase sets
  # to permissive) may log denials that are not in scope here.
  denials=$("${SSH[@]}" "root@$ip" 'ausearch --input-logs -m AVC,USER_AVC,SELINUX_ERR -ts boot 2>/dev/null \
    | grep -E "^type=(AVC|USER_AVC|SELINUX_ERR)" | grep -c -E "scontext=[^ ]*:(patroni_t|postgresql_t):"')
  [ "${denials:-0}" -eq 0 ] || fail "$ip: $denials SELinux denials for patroni_t/postgresql_t since boot"
done

[ "$failures" -eq 0 ] && echo "SELinux checks passed" || exit 1
