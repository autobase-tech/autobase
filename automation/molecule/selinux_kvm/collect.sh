#!/usr/bin/env bash
# Collect the SELinux state of every node into <out dir> and a summary for the job.
#
# Usage: collect.sh <inventory file> <out dir> <label>
set -uo pipefail

INVENTORY="$1"
OUT="$2"
LABEL="$3"
SSH=(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)

mkdir -p "$OUT"
ips=$(awk '/^\[master\]|^\[replica\]/{f=1;next} /^\[/{f=0} f && NF {print $1}' "$INVENTORY")

{
  echo "## SELinux: $LABEL"
  echo
  for ip in $ips; do
    "${SSH[@]}" "root@$ip" 'command -v audit2allow >/dev/null || dnf -q -y install policycoreutils-python-utils >/dev/null' || true
    "${SSH[@]}" "root@$ip" 'ausearch --input-logs -m AVC,USER_AVC,SELINUX_ERR -ts boot 2>/dev/null' >"$OUT/$ip-$LABEL-avc.log"
    "${SSH[@]}" "root@$ip" 'for unit in patroni etcd consul vip-manager pgbouncer haproxy confd keepalived; do
        systemctl cat $unit >/dev/null 2>&1 || continue; echo "== $unit"; journalctl -b --no-pager -u $unit | tail -60; done
      tail -n 200 /var/log/postgresql/*.log 2>/dev/null;
      ss -ltnp; echo "auditd: $(systemctl is-active auditd)"; journalctl -k -b --no-pager | grep "avc:"' \
      >"$OUT/$ip-$LABEL-services.log" 2>&1
    count=$(grep -c '^type=AVC' "$OUT/$ip-$LABEL-avc.log" || true)
    echo "### $ip: $("${SSH[@]}" "root@$ip" getenforce), $count AVC records"
    echo
    echo '```'
    "${SSH[@]}" "root@$ip" "ps -eZ | grep -E 'postgres|patroni|etcd|haproxy|pgbouncer|confd' | awk '{print \$1, \$NF}' | sort -u"
    "${SSH[@]}" "root@$ip" 'ls -Zd /pgdata /pgdata/18/main /pgwal /pgwal/18/pg_wal 2>/dev/null'
    echo '```'
    if [ "$count" -gt 0 ]; then
      echo
      echo '<details><summary>audit2allow</summary>'
      echo
      echo '```'
      "${SSH[@]}" "root@$ip" 'ausearch --input-logs -m AVC -ts boot 2>/dev/null | audit2allow' | tee "$OUT/$ip-$LABEL-audit2allow.te"
      echo '```'
      echo '</details>'
    fi
    echo
  done
} | tee -a "$OUT/summary.md"
