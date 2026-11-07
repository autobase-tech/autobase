#!/usr/bin/env bash
# Run on a cluster node: switch over from pgnode01 to the synchronous standby through the
# Patroni REST API (works with either DCS, with or without TLS).
set -euo pipefail

ip=$(hostname -I | cut -d' ' -f1)
creds=$(python3 -c "
import yaml
auth = yaml.safe_load(open('/etc/patroni/patroni.yml'))['restapi'].get('authentication', {})
print(auth.get('username', '') + ':' + auth.get('password', ''))")
api() { curl -fsSk "https://$ip:8008$1" "${@:2}" 2>/dev/null || curl -fsS "http://$ip:8008$1" "${@:2}"; }

candidate=$(api /cluster | python3 -c "
import json, sys
print(next(m['name'] for m in json.load(sys.stdin)['members'] if m['role'] == 'sync_standby'))")
api /switchover -u "$creds" -X POST -H 'Content-Type: application/json' \
  -d "{\"leader\": \"pgnode01\", \"candidate\": \"$candidate\"}"
echo
sleep 20
api /cluster | python3 -c "
import json, sys
for m in json.load(sys.stdin)['members']:
    print(m['name'], m['role'], m['state'], m.get('timeline'))"
