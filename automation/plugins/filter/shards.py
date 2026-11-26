"""Resolve a fixed PgDog topology from the complete PostgreSQL inventory."""

import re

from ansible.errors import AnsibleFilterError


def cloud_shard_placement(server_name, shards_count, servers_per_shard):
    """Generate cloud VM names in replica order, then by shard."""
    return {
        f"{server_name}-shard{shard}-pg{node:02d}": {
            "shard_id": shard,
            "role": "master" if node == 1 else "replica",
        }
        for node in range(1, servers_per_shard + 1)
        for shard in range(shards_count)
    }


def shard_topology(groups, hostvars, target="all"):
    hosts = groups.get("postgres_cluster", [])
    explicit = any("shard_id" in hostvars[host] for host in hosts)
    by_host = {}
    members = {}
    bootstrap = {}
    for host in hosts:
        shard = hostvars[host].get("shard_id") if explicit else 0
        if not isinstance(shard, int) or isinstance(shard, bool) or shard < 0:
            raise AnsibleFilterError(f"{host}: shard_id must be a non-negative integer")
        by_host[host] = shard
        members.setdefault(shard, []).append(host)
    ids = sorted(members)
    if ids != list(range(len(ids))):
        raise AnsibleFilterError("PgDog shard numbers must be contiguous starting at 0")
    selected_ids = ids
    selected = hosts
    if target != "all":
        # Ansible's -e target_shard=0 supplies a string, while YAML supplies an integer.
        if not re.fullmatch(r"0|[1-9][0-9]*", str(target)) or int(target) not in members:
            raise AnsibleFilterError(f"Unknown target_shard: {target}")
        target_id = int(target)
        selected_ids = [target_id]
        selected = members[target_id]
    masters = set(groups.get("master", []))
    replicas = set(groups.get("replica", []))
    if explicit:
        for shard, nodes in members.items():
            first = [host for host in nodes if host in masters]
            if len(first) != 1 or any((host in masters) == (host in replicas) for host in nodes):
                raise AnsibleFilterError(f"shard{shard}: expected one master and all other members in replica")
            bootstrap[shard] = first[0]
    return {
        "explicit": explicit,
        "ids": ids,
        "members": members,
        "by_host": by_host,
        "bootstrap": bootstrap,
        "selected_ids": selected_ids,
        "selected": selected,
    }


class FilterModule:
    def filters(self):
        return {
            "cloud_shard_placement": cloud_shard_placement,
            "shard_topology": shard_topology,
        }
