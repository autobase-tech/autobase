#!/usr/bin/env bash
# Print the address of the current Patroni leader, asking the REST API of the first node
# (HTTPS with the default tls_cert_generate: true, HTTP without).
#
# Usage: leader.sh <inventory file>
set -euo pipefail

first=$(awk '/^\[master\]/{getline; print $1}' "$1")
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "root@$first" \
  "curl -fsSk https://$first:8008/cluster || curl -fsS http://$first:8008/cluster" \
  | python3 -c "import json, sys; print(next(m['host'] for m in json.load(sys.stdin)['members'] if m['role'] == 'leader'))"
