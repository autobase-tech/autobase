"""Failure and cancellation coverage for the cluster maintenance coordinator."""

import importlib.util
import signal
import threading
import time
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


MODULE_PATH = Path(__file__).resolve().parents[4] / 'plugins/modules/pgdog_maintenance.py'
SPEC = importlib.util.spec_from_file_location('pgdog_maintenance', MODULE_PATH)
maintenance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(maintenance)


def parameters(**overrides):
    params = dict(servers=['127.0.0.1', '127.0.0.2', '127.0.0.3'], state='enabled',
                  pgdog_port=6432, admin_user='admin', postgres_port=5432, postgres_user='postgres',
                  passfile='/tmp/pgdog-test.pgpass', command_timeout=0.03, terminate_after=30,
                  timeout=0.02, query_age_threshold=100, resume_retries=3, resume_delay=0)
    params.update(overrides)
    return params


class Cluster:
    """Model buffered BEGIN, backend waiters, partial acknowledgements and transient failures."""

    def __init__(self, controller, **plan):
        self.controller = controller
        self.plan = plan
        self.calls = {}
        self.paused = dict.fromkeys(controller.servers, False)
        self.terminated = set()
        self.events = []
        self.lock = threading.Lock()
        controller.query = self.query
        wait = controller.cancelled.wait
        controller.cancelled.wait = lambda delay: wait(min(delay, 0.001))

    def query(self, server, sql, admin=True, arguments=None, columns=(), cancellable=True):
        action = sql if sql in ('MAINTENANCE ON', 'MAINTENANCE OFF', 'SHOW CLIENTS state', 'SHOW POOLS') else (
            'terminate' if sql == maintenance.TERMINATE_QUERY else 'postgres')
        with self.lock:
            key = (server, action)
            index = self.calls.get(key, 0)
            self.calls[key] = index + 1
            self.events.append((action, 'start', time.monotonic(), server))
        time.sleep(self.plan.get('on_delays', {}).get(server, 0) if action == 'MAINTENANCE ON' else 0)
        failure = None
        rows = []
        with self.lock:
            if action == 'MAINTENANCE ON':
                self.paused[server] = True  # The command may take effect even if its acknowledgement is lost.
                if server in self.plan.get('fail_on', ()):
                    failure = 'Lost maintenance acknowledgement'
            elif action == 'MAINTENANCE OFF':
                if cancellable:
                    raise AssertionError('Compensation must not be cancelled')
                if index < self.plan.get('off_failures', {}).get(server, 0):
                    failure = 'Cannot disable maintenance'
                else:
                    self.paused[server] = False
            elif action == 'SHOW CLIENTS state':
                states = self.plan.get('clients', {}).get(server, ['idle'])
                state = states[min(index, len(states) - 1)]
                rows = [dict(user='admin', database='admin', state='active'),
                        dict(user='app', database='app', state=state)]
                if server in self.plan.get('fail_poll', ()):
                    failure = 'Cannot read client activity'
            elif action == 'SHOW POOLS':
                counts = self.plan.get('waiting', {}).get(server, [0])
                rows = [dict(cl_waiting=counts[min(index, len(counts) - 1)])]
            elif action == 'postgres':
                rows = [dict(active=int(self.plan.get('active', False) and server not in self.terminated))]
            else:
                if arguments != (self.controller.params['query_age_threshold'],):
                    raise AssertionError('Query age must be passed as a bound parameter')
                if server in self.plan.get('fail_terminate', ()):
                    failure = 'Cannot terminate sessions'
                elif self.plan.get('active'):
                    self.terminated.add(server)
                    rows = [dict(terminated=True)]
            self.events.append((action, 'end', time.monotonic(), server))
        if failure:
            raise maintenance.MaintenanceError(failure)
        return rows


class CoordinatorTests(unittest.TestCase):
    def setup_cluster(self, params=None, **plan):
        controller = maintenance.PgDogMaintenance(parameters(**(params or {})))
        return controller, Cluster(controller, **plan)

    def assert_resumed(self, cluster):
        self.assertFalse(any(cluster.paused.values()))

    def test_success_keeps_every_instance_paused(self):
        controller, cluster = self.setup_cluster()
        controller.run()
        self.assertTrue(all(cluster.paused.values()))
        self.assertFalse(any(action == 'MAINTENANCE OFF' for action, _, _, _ in cluster.events))
        enabled = [at for action, event, at, _ in cluster.events if action == 'MAINTENANCE ON' and event == 'end']
        checked = [at for action, event, at, _ in cluster.events if action == 'SHOW CLIENTS state' and event == 'start']
        self.assertGreaterEqual(min(checked), max(enabled))

    def test_partial_failure_waits_for_late_success_before_compensation(self):
        controller, cluster = self.setup_cluster(fail_on=['127.0.0.2'], on_delays={'127.0.0.1': 0.03})
        with self.assertRaises(maintenance.MaintenanceError) as caught:
            controller.run()
        self.assertIn('127.0.0.2', caught.exception.errors)
        enabled = [at for action, event, at, _ in cluster.events if action == 'MAINTENANCE ON' and event == 'end']
        resumed = [at for action, event, at, _ in cluster.events if action == 'MAINTENANCE OFF' and event == 'start']
        self.assertGreaterEqual(min(resumed), max(enabled))
        self.assert_resumed(cluster)

    def test_poll_failure_cancels_pause(self):
        controller, cluster = self.setup_cluster(fail_poll=['127.0.0.2'])
        with self.assertRaises(maintenance.MaintenanceError):
            controller.run()
        self.assert_resumed(cluster)

    def test_buffered_begin_without_backend_prevents_success(self):
        controller, cluster = self.setup_cluster(params={'terminate_after': 0},
                                                 clients={'127.0.0.2': ['idle in transaction']})
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'did not drain'):
            controller.run()
        self.assertEqual(sum(controller.terminated.values()), 0)
        self.assert_resumed(cluster)

    def test_buffered_begin_can_finish_during_grace_period(self):
        controller, cluster = self.setup_cluster(clients={'127.0.0.2': ['idle in transaction', 'idle']})
        controller.run()
        self.assertEqual(cluster.calls[('127.0.0.2', 'SHOW CLIENTS state')], 2)
        self.assertTrue(all(cluster.paused.values()))

    def test_checkout_waiters_must_drain(self):
        controller, cluster = self.setup_cluster(clients={'127.0.0.2': ['waiting']},
                                                 waiting={'127.0.0.2': [1, 0]})
        controller.run()
        self.assertEqual(cluster.calls[('127.0.0.2', 'SHOW POOLS')], 2)

    def test_maintenance_waiters_do_not_prevent_success(self):
        controller, cluster = self.setup_cluster(clients={'127.0.0.2': ['waiting']})
        controller.run()
        self.assertEqual(cluster.calls[('127.0.0.2', 'SHOW POOLS')], 1)

    def test_invalid_pool_counts_abort_instead_of_looking_idle(self):
        for value in (-1, None, 'invalid', Decimal('0.5')):
            with self.subTest(value=value):
                controller, cluster = self.setup_cluster(waiting={'127.0.0.2': [value]})
                with self.assertRaises(maintenance.MaintenanceError):
                    controller.run()
                self.assert_resumed(cluster)

    def test_termination_allows_backend_transactions_to_drain(self):
        controller, cluster = self.setup_cluster(params={'terminate_after': 0}, active=True)
        controller.run()
        self.assertEqual(set(cluster.terminated), set(controller.servers))
        self.assertEqual(sum(controller.terminated.values()), 3)

    def test_termination_failure_cancels_pause(self):
        controller, cluster = self.setup_cluster(params={'terminate_after': 0}, active=True,
                                                 fail_terminate=['127.0.0.2'])
        with self.assertRaises(maintenance.MaintenanceError):
            controller.run()
        self.assert_resumed(cluster)

    def test_resume_retries_only_failed_instances(self):
        controller, cluster = self.setup_cluster(params={'state': 'disabled'}, off_failures={'127.0.0.2': 2})
        controller.run()
        self.assertEqual(cluster.calls[('127.0.0.2', 'MAINTENANCE OFF')], 3)
        self.assertEqual(cluster.calls[('127.0.0.1', 'MAINTENANCE OFF')], 1)

    def test_permanent_resume_failure_is_reported(self):
        controller, cluster = self.setup_cluster(params={'state': 'disabled'}, off_failures={'127.0.0.2': 10})
        with self.assertRaises(maintenance.MaintenanceError) as caught:
            controller.run()
        self.assertEqual(list(caught.exception.errors), ['127.0.0.2'])
        self.assertEqual(cluster.calls[('127.0.0.2', 'MAINTENANCE OFF')], 4)

    def test_compensation_preserves_original_and_cleanup_errors(self):
        controller, cluster = self.setup_cluster(fail_on=['127.0.0.2'], off_failures={'127.0.0.3': 10})
        with self.assertRaises(maintenance.MaintenanceError) as caught:
            controller.run()
        self.assertIn('127.0.0.2', caught.exception.errors)
        self.assertIn('127.0.0.3', controller.cleanup_errors)

    def test_cancellation_waits_for_pending_enable_operations(self):
        controller, cluster = self.setup_cluster(on_delays={'127.0.0.1': 0.03, '127.0.0.2': 0.02})
        timer = threading.Timer(0.005, controller.cancelled.set)
        timer.start()
        try:
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'interrupted'):
                controller.run()
        finally:
            timer.join()
        enabled = [at for action, event, at, _ in cluster.events if action == 'MAINTENANCE ON' and event == 'end']
        resumed = [at for action, event, at, _ in cluster.events if action == 'MAINTENANCE OFF' and event == 'start']
        self.assertGreaterEqual(min(resumed), max(enabled))
        self.assert_resumed(cluster)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.controller = maintenance.PgDogMaintenance(parameters())
        self.constants = SimpleNamespace(POLL_OK=0, POLL_READ=1, POLL_WRITE=2)
        self.driver = MagicMock()
        self.connection = self.driver.connect.return_value
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.driver_patch = patch.object(maintenance, 'psycopg2', self.driver)
        self.constants_patch = patch.object(maintenance, 'extensions', self.constants, create=True)
        self.driver_patch.start()
        self.constants_patch.start()
        self.addCleanup(self.driver_patch.stop)
        self.addCleanup(self.constants_patch.stop)

    def test_async_query_has_no_implicit_begin_and_closes_connection(self):
        self.connection.poll.side_effect = [1, 2, 0, 1, 0]
        self.cursor.description = [('active',)]
        self.cursor.fetchall.return_value = [(0,)]
        with patch.object(maintenance.select, 'select'):
            rows = self.controller.query('127.0.0.1', maintenance.ACTIVE_QUERY, admin=False, columns=('active',))
        self.assertEqual(rows, [dict(active=0)])
        kwargs = self.driver.connect.call_args.kwargs
        self.assertTrue(kwargs['async_'])
        self.assertEqual(kwargs['hostaddr'], '127.0.0.1')
        self.assertEqual(kwargs['passfile'], '/tmp/pgdog-test.pgpass')
        self.cursor.execute.assert_called_once_with(maintenance.ACTIVE_QUERY, None)
        self.connection.close.assert_called_once()

    def test_hung_query_is_bounded_and_connection_is_closed(self):
        self.connection.poll.side_effect = [0] + [1] * 100000
        start = time.monotonic()
        with patch.object(maintenance.select, 'select', side_effect=lambda *args: time.sleep(0.001)):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'timed out'):
                self.controller.query('127.0.0.1', 'MAINTENANCE ON')
        self.assertLess(time.monotonic() - start, 0.5)
        self.connection.close.assert_called_once()

    def test_missing_result_columns_do_not_mean_zero_activity(self):
        self.connection.poll.return_value = 0
        self.cursor.description = [('unrelated',)]
        with self.assertRaisesRegex(maintenance.MaintenanceError, 'Missing activity columns'):
            self.controller.query('127.0.0.1', 'SHOW POOLS', columns=('cl_waiting',))
        self.connection.close.assert_called_once()

    def test_cancellation_during_query_closes_connection(self):
        self.connection.poll.side_effect = [0, 1, 1]
        with patch.object(maintenance.select, 'select', side_effect=lambda *args: self.controller.cancelled.set()):
            with self.assertRaisesRegex(maintenance.MaintenanceError, 'interrupted'):
                self.controller.query('127.0.0.1', 'MAINTENANCE ON')
        self.connection.close.assert_called_once()


class ModuleResult(BaseException):
    def __init__(self, **result):
        self.result = result


class ModuleTests(unittest.TestCase):
    def invoke(self, params=None, check_mode=False, controller=None, driver=True):
        fake_module = MagicMock()
        fake_module.params = parameters(**(params or {}))
        fake_module.check_mode = check_mode
        fake_module.exit_json.side_effect = lambda **kwargs: self.finish(False, **kwargs)
        fake_module.fail_json.side_effect = lambda **kwargs: self.finish(True, **kwargs)
        with patch.object(maintenance, 'AnsibleModule', return_value=fake_module), \
                patch.object(maintenance, 'psycopg2', driver), \
                patch.object(maintenance, 'PgDogMaintenance', return_value=controller) as factory:
            with self.assertRaises(ModuleResult) as caught:
                maintenance.main()
        return caught.exception.result, factory

    @staticmethod
    def finish(failed, **result):
        raise ModuleResult(failed=failed, **result)

    def test_check_mode_does_not_change_maintenance(self):
        result, factory = self.invoke(check_mode=True)
        self.assertFalse(result['failed'])
        factory.assert_not_called()

    def test_invalid_parameters_fail_before_connecting(self):
        for params in ({'servers': []}, {'servers': ['database.example']}, {'timeout': 0},
                       {'command_timeout': -1}, {'pgdog_port': 70000}, {'resume_retries': -1}):
            with self.subTest(params=params):
                result, factory = self.invoke(params)
                self.assertTrue(result['failed'])
                factory.assert_not_called()

    def test_signal_handlers_are_restored_on_failure(self):
        signals = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
        previous = {signum: signal.getsignal(signum) for signum in signals}
        controller = MagicMock(changed=True, activity={}, terminated={}, cleanup_errors={})
        controller.run.side_effect = maintenance.MaintenanceError('Failed to drain', {'127.0.0.2': 'timeout'})
        result, _ = self.invoke(controller=controller)
        self.assertTrue(result['failed'])
        self.assertEqual(result['errors'], {'127.0.0.2': 'timeout'})
        self.assertEqual(previous, {signum: signal.getsignal(signum) for signum in signals})


if __name__ == '__main__':
    unittest.main()
