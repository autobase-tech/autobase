"""Inventory invariants used by deployment, routing and maintenance playbooks."""

import importlib.util
import unittest
from pathlib import Path

from ansible.errors import AnsibleFilterError


module_path = Path(__file__).resolve().parents[4] / "plugins/filter/shards.py"
spec = importlib.util.spec_from_file_location("shards", module_path)
shards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shards)


class ShardTopologyTests(unittest.TestCase):
    def setUp(self):
        self.groups = {
            "postgres_cluster": ["b", "a", "c", "d"],
            "master": ["a", "b"],
            "replica": ["c", "d"],
        }
        self.members = {
            "a": {"shard_id": 0}, "b": {"shard_id": 1},
            "c": {"shard_id": 0}, "d": {"shard_id": 1},
        }

    def test_target_keeps_full_topology(self):
        complete_topology = shards.shard_topology(self.groups, self.members)
        self.assertEqual(complete_topology["selected_ids"], [0, 1])
        for target in (1, "1"):
            with self.subTest(target=target):
                topology = shards.shard_topology(self.groups, self.members, target)
                self.assertEqual(topology["ids"], [0, 1])
                self.assertEqual(topology["selected_ids"], [1])
                self.assertEqual(topology["selected"], ["b", "d"])
                self.assertEqual(topology["bootstrap"], {1: "b", 0: "a"})
                self.assertEqual(topology["members"][0], ["a", "c"])

    def test_zero_is_a_valid_target(self):
        topology = shards.shard_topology(self.groups, self.members, 0)
        self.assertEqual(topology["selected_ids"], [0])
        self.assertEqual(topology["selected"], ["a", "c"])

    def test_legacy_inventory(self):
        hosts = {host: {} for host in self.members}
        topology = shards.shard_topology(self.groups, hosts, "0")
        self.assertFalse(topology["explicit"])
        self.assertEqual(topology["selected"], self.groups["postgres_cluster"])

    def test_cloud_placement_preserves_existing_shards_when_adding_servers(self):
        placement = shards.cloud_shard_placement("orders-db", 4, 3)
        expanded = shards.cloud_shard_placement("orders-db", 4, 4)

        self.assertEqual(list(expanded)[:len(placement)], list(placement))
        self.assertEqual({name: expanded[name] for name in placement}, placement)
        self.assertEqual(list(placement)[:4], [f"orders-db-shard{shard}-pg01" for shard in range(4)])
        for shard_id in range(4):
            roles = [node["role"] for node in placement.values() if node["shard_id"] == shard_id]
            self.assertEqual(roles, ["master", "replica", "replica"])
            self.assertEqual(expanded[f"orders-db-shard{shard_id}-pg04"], {"shard_id": shard_id, "role": "replica"})

    def test_invalid_assignments(self):
        for value in [{}, {"shard_id": None}, {"shard_id": "0"}, {"shard_id": True}, {"shard_id": -1}]:
            with self.subTest(value=value), self.assertRaises(AnsibleFilterError):
                shards.shard_topology(self.groups, {**self.members, "a": value})

    def test_gaps_and_unknown_target(self):
        with self.assertRaisesRegex(AnsibleFilterError, "contiguous"):
            shards.shard_topology(self.groups, {k: {"shard_id": 1} for k in self.members})
        for target in (2, "01", "shard1"):
            with self.subTest(target=target), self.assertRaisesRegex(AnsibleFilterError, "target_shard"):
                shards.shard_topology(self.groups, self.members, target)

    def test_ambiguous_bootstrap_or_replica(self):
        for roles in [{"master": ["a"]}, {"replica": ["a", "c", "d"]}, {"master": ["a", "b", "d"]}]:
            with self.subTest(roles=roles), self.assertRaises(AnsibleFilterError):
                shards.shard_topology({**self.groups, **roles}, self.members)
