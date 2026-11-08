#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: pgdog_maintenance
short_description: Hold and drain client transactions across PgDog instances
description:
  - Enables maintenance on all instances before waiting for PgDog clients, backend checkout queues and PostgreSQL activity to drain.
  - On failure, waits for pending operations and attempts to disable maintenance on every instance.
  - Uses direct, asynchronous PostgreSQL connections with a deadline covering connection establishment and query execution.
  - Disabling maintenance is retried; failure is reported for each affected instance.
  - Maintenance commands are idempotent, but the module reports changed because PgDog does not expose its maintenance flag.
options:
  servers:
    description: IP addresses of the database servers running PgDog.
    required: true
    type: list
    elements: str
  state:
    description: Enable maintenance and drain transactions, or disable maintenance.
    required: true
    type: str
    choices: [enabled, disabled]
  pgdog_port:
    description: PgDog admin port.
    type: int
    default: 6432
  admin_user:
    description: PgDog admin user. The admin database is C(admin).
    type: str
    default: admin
  postgres_port:
    description: PostgreSQL port.
    type: int
    default: 5432
  postgres_user:
    description: PostgreSQL superuser for activity checks and session termination.
    type: str
    default: postgres
  passfile:
    description: Path to a libpq password file containing credentials for both services.
    required: true
    type: path
  command_timeout:
    description: Maximum connection and query duration, in seconds, for each command.
    type: int
    default: 5
  terminate_after:
    description: Start terminating PostgreSQL sessions after this many seconds of draining.
    type: int
    default: 30
  timeout:
    description: Abort draining after this many seconds. Starts after maintenance is enabled everywhere.
    type: int
    default: 60
  query_age_threshold:
    description: Minimum age of the last query, in milliseconds, for terminating a PostgreSQL session.
    type: int
    default: 100
  resume_retries:
    description: Additional attempts to disable maintenance on each instance.
    type: int
    default: 3
  resume_delay:
    description: Delay between attempts to disable maintenance, in seconds.
    type: int
    default: 2
requirements:
  - psycopg2 >= 2.7
"""

EXAMPLES = r"""
- name: Hold and drain client transactions on all PgDog instances
  vitabaks.autobase.pgdog_maintenance:
    servers: [10.0.0.1, 10.0.0.2, 10.0.0.3]
    state: enabled
    admin_user: admin
    postgres_user: postgres
    passfile: /var/lib/postgresql/.pgpass

- name: Resume client transactions
  vitabaks.autobase.pgdog_maintenance:
    servers: [10.0.0.1]
    state: disabled
    passfile: /var/lib/postgresql/.pgpass
"""

RETURN = r"""
activity:
  description: Last activity counts per server, including PgDog clients, checkout waiters and PostgreSQL sessions.
  returned: when draining was checked
  type: dict
terminated:
  description: Number of PostgreSQL sessions signalled for termination per server.
  returned: always
  type: dict
errors:
  description: Operation errors keyed by server address.
  returned: on failure
  type: dict
cleanup_errors:
  description: Instances where maintenance could not be disabled after a failed pause.
  returned: on failure
  type: dict
"""

import ipaddress
import select
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    import psycopg2
    from psycopg2 import extensions
except ImportError:
    psycopg2 = None


ACTIVE_QUERY = """SELECT count(*) AS active FROM pg_stat_activity
WHERE pid <> pg_backend_pid() AND state <> 'idle' AND backend_type = 'client backend'
"""
TERMINATE_QUERY = """SELECT pg_terminate_backend(pid) AS terminated FROM pg_stat_activity
WHERE pid <> pg_backend_pid() AND state <> 'idle' AND backend_type = 'client backend'
AND query_start < clock_timestamp() - (%s * interval '1 millisecond')
"""


class MaintenanceError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or {}


def activity_count(value):
    count = int(value)
    if isinstance(value, bool) or count < 0 or count != value:
        raise ValueError("Invalid activity count")
    return count


class PgDogMaintenance:
    def __init__(self, params):
        self.params = params
        self.servers = list(dict.fromkeys(params['servers']))
        self.cancelled = threading.Event()
        self.changed = False
        self.activity = {}
        self.terminated = dict.fromkeys(self.servers, 0)
        self.cleanup_errors = {}

    def wait(self, connection, deadline, cancellable):
        while True:
            if cancellable and self.cancelled.is_set():
                raise MaintenanceError("Maintenance operation interrupted")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MaintenanceError("Connection or query timed out")
            state = connection.poll()
            if state == extensions.POLL_OK:
                return
            readers = [connection] if state == extensions.POLL_READ else []
            writers = [connection] if state == extensions.POLL_WRITE else []
            if not readers and not writers:
                raise MaintenanceError("Unexpected connection poll state")
            select.select(readers, writers, [], min(remaining, 0.2))

    def query(self, server, sql, admin=True, arguments=None, columns=(), cancellable=True):
        if cancellable and self.cancelled.is_set():
            raise MaintenanceError("Maintenance operation interrupted")
        deadline = time.monotonic() + self.params['command_timeout']
        # Numeric hostaddr avoids blocking DNS resolution outside the asynchronous deadline.
        connection = psycopg2.connect(
            host=server, hostaddr=server, async_=True, passfile=self.params['passfile'],
            port=self.params['pgdog_port'] if admin else self.params['postgres_port'],
            user=self.params['admin_user'] if admin else self.params['postgres_user'],
            dbname='admin' if admin else 'postgres', application_name='autobase_pgdog_maintenance',
        )
        try:
            self.wait(connection, deadline, cancellable)
            with connection.cursor() as cursor:
                cursor.execute(sql, arguments)
                self.wait(connection, deadline, cancellable)
                fields = [column[0] for column in cursor.description or ()]
                if not set(columns).issubset(fields):
                    raise MaintenanceError("Missing activity columns in query result")
                rows = [dict(zip(fields, row)) for row in cursor.fetchall()] if fields else []
                if any(row[column] is None for row in rows for column in columns):
                    raise MaintenanceError("Incomplete activity row in query result")
                return rows
        finally:
            connection.close()

    def batch(self, operation):
        results, errors = {}, {}
        # Collect every result, including late successes after another instance failed.
        with ThreadPoolExecutor(max_workers=len(self.servers)) as executor:
            pending = {executor.submit(operation, server): server for server in self.servers}
            for future in as_completed(pending):
                server = pending[future]
                try:
                    results[server] = future.result()
                except Exception as error:
                    errors[server] = str(error)
        return results, errors

    def disable(self, server):
        for attempt in range(self.params['resume_retries'] + 1):
            try:
                # Compensation must finish even when cancellation triggered the original failure.
                self.query(server, 'MAINTENANCE OFF', cancellable=False)
                return
            except Exception:
                if attempt == self.params['resume_retries']:
                    raise
                time.sleep(self.params['resume_delay'])

    def count_activity(self, server):
        clients = self.query(server, 'SHOW CLIENTS state', columns=('user', 'database', 'state'))
        client_count = sum(
            row['state'] not in ('idle', 'waiting', 'disconnected', 'force close') for row in clients
            if not (row['database'] == 'admin' and row['user'] == self.params['admin_user'])
        )
        # Client 'waiting' includes both maintenance and checkout waits. Only the latter must drain.
        pools = self.query(server, 'SHOW POOLS', columns=('cl_waiting',))
        waiting = sum(activity_count(row['cl_waiting']) for row in pools)
        postgres = self.query(server, ACTIVE_QUERY, admin=False, columns=('active',))
        if len(postgres) != 1:
            raise MaintenanceError("Expected one PostgreSQL activity count")
        return dict(clients=client_count, waiting=waiting, postgres=activity_count(postgres[0]['active']))

    def terminate(self, server):
        rows = self.query(server, TERMINATE_QUERY, admin=False,
                          arguments=(self.params['query_age_threshold'],), columns=('terminated',))
        return sum(row['terminated'] is True for row in rows)

    def run(self):
        self.changed = True
        if self.params['state'] == 'disabled':
            _, errors = self.batch(self.disable)
            if errors or self.cancelled.is_set():
                raise MaintenanceError("Could not complete disabling PgDog maintenance", errors)
            return

        try:
            _, errors = self.batch(lambda server: self.query(server, 'MAINTENANCE ON'))
            if errors:
                raise MaintenanceError("Could not enable maintenance on every PgDog", errors)
            start = time.monotonic()
            while True:
                if self.cancelled.is_set():
                    raise MaintenanceError("Maintenance operation interrupted")
                self.activity, errors = self.batch(self.count_activity)
                if errors:
                    raise MaintenanceError("Could not check cluster activity", errors)
                if self.cancelled.is_set():
                    raise MaintenanceError("Maintenance operation interrupted")
                if not any(sum(counts.values()) for counts in self.activity.values()):
                    return
                elapsed = time.monotonic() - start
                if elapsed >= self.params['timeout']:
                    raise MaintenanceError("Client transactions did not drain before the timeout")
                if elapsed >= self.params['terminate_after']:
                    terminated, errors = self.batch(self.terminate)
                    for server, count in terminated.items():
                        self.terminated[server] += count
                    if errors:
                        raise MaintenanceError("Could not terminate PostgreSQL sessions", errors)
                self.cancelled.wait(1)
        except Exception:
            _, self.cleanup_errors = self.batch(self.disable)
            raise


def main():
    module = AnsibleModule(
        argument_spec=dict(
            servers=dict(type='list', elements='str', required=True),
            state=dict(type='str', choices=['enabled', 'disabled'], required=True),
            pgdog_port=dict(type='int', default=6432),
            admin_user=dict(type='str', default='admin'),
            postgres_port=dict(type='int', default=5432),
            postgres_user=dict(type='str', default='postgres'),
            passfile=dict(type='path', required=True),
            command_timeout=dict(type='int', default=5),
            terminate_after=dict(type='int', default=30),
            timeout=dict(type='int', default=60),
            query_age_threshold=dict(type='int', default=100),
            resume_retries=dict(type='int', default=3),
            resume_delay=dict(type='int', default=2),
        ),
        supports_check_mode=True,
    )
    params = module.params
    if not params['servers']:
        module.fail_json(msg="At least one server is required")
    for server in params['servers']:
        try:
            ipaddress.ip_address(server)
        except ValueError:
            module.fail_json(msg="servers must contain IP addresses: {0}".format(server))
    for name in ('pgdog_port', 'postgres_port'):
        if not 1 <= params[name] <= 65535:
            module.fail_json(msg="{0} must be between 1 and 65535".format(name))
    for name in ('command_timeout', 'timeout'):
        if params[name] <= 0:
            module.fail_json(msg="{0} must be positive".format(name))
    for name in ('terminate_after', 'query_age_threshold', 'resume_retries', 'resume_delay'):
        if params[name] < 0:
            module.fail_json(msg="{0} must not be negative".format(name))
    if psycopg2 is None:
        module.fail_json(msg=missing_required_lib('psycopg2'))
    if module.check_mode:
        module.exit_json(changed=True, state=params['state'], servers=params['servers'])

    maintenance = PgDogMaintenance(params)
    previous_handlers = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous_handlers[signum] = signal.signal(signum, lambda _signum, _frame: maintenance.cancelled.set())
        try:
            maintenance.run()
        except Exception as error:
            module.fail_json(msg=str(error), changed=maintenance.changed,
                             errors=getattr(error, 'errors', {}), cleanup_errors=maintenance.cleanup_errors,
                             activity=maintenance.activity, terminated=maintenance.terminated)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    module.exit_json(changed=maintenance.changed, state=params['state'], servers=maintenance.servers,
                     activity=maintenance.activity, terminated=maintenance.terminated)


if __name__ == '__main__':
    main()
