#!/usr/bin/env bash
# Run on each PgDog node, before and after switchover (vars_pgdog.yml).
set -euo pipefail

export PGPASSWORD=db1_user-test-pass PGSSLMODE=require PGCONNECT_TIMEOUT=10
PSQL=(psql -h 127.0.0.1 -p 16432 -U db1_user -d db1 -v ON_ERROR_STOP=1 -At)

# Re-read the configuration and TLS files from pgdog_t and start a new process.
systemctl reload pgdog
systemctl restart pgdog
ps -C pgdog -o label= | cut -d: -f3 | sort -u | grep -x pgdog_t

# Every instance must route writes to the primary, regardless of the local node's role.
"${PSQL[@]}" -c 'CREATE TABLE IF NOT EXISTS pgdog_selinux_test (id int); INSERT INTO pgdog_selinux_test VALUES (1) RETURNING id' \
  | grep -x 1
"${PSQL[@]}" -c 'SELECT 1' | grep -x 1

if PGSSLMODE=disable "${PSQL[@]}" -c 'SELECT 1'; then
  echo 'FAIL PgDog accepted a client without TLS'
  exit 1
fi

# Replicas can be banned briefly after restart; wait for role/lag detection.
replica=false
for _ in $(seq 1 12); do
  roles=$(for _ in $(seq 1 10); do "${PSQL[@]}" -c 'SELECT pg_is_in_recovery()' || exit 1; done)
  if echo "$roles" | grep -qx t; then replica=true; break; fi
  sleep 5
done
[ "$replica" = true ] || { echo 'FAIL PgDog did not route reads to a replica'; exit 1; }

curl -fsS --max-time 10 --retry 12 --retry-delay 5 --retry-all-errors http://127.0.0.1:18081/ | grep -x up
# Consume the entire metrics response so curl cannot fail with a broken pipe.
curl -fsS --max-time 10 http://127.0.0.1:19090/metrics | grep '^#' >/dev/null
