#!/usr/bin/env bash
# Print the address of the current Patroni leader, asking the REST API of the first node
# (HTTPS with the default tls_cert_generate: true, HTTP without).
#
# Usage: leader.sh <inventory file>
set -euo pipefail

first=$(awk '/^\[master\]/{getline; print $1}' "$1")
cluster=$(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "root@$first" bash -s -- "$first" <<'REMOTE'
set -euo pipefail
port=$(python3 -c "
import yaml
print(yaml.safe_load(open('/etc/patroni/patroni.yml'))['restapi']['listen'].rsplit(':', 1)[1])")
curl -fsSk "https://$1:$port/cluster" || curl -fsS "http://$1:$port/cluster"
REMOTE
)
echo "$cluster" \
  | python3 -c "import json, sys; print(next(m['host'] for m in json.load(sys.stdin)['members'] if m['role'] == 'leader'))"
