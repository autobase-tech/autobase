#!/usr/bin/python
# -*- coding: utf-8 -*-

# Temporary workaround until community.aws.elb_network_lb supports modifying subnets of an existing
# Network Load Balancer (it currently fails with "Modifying subnets ... is not supported").

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: aws_nlb_subnets
short_description: Add Availability Zones to an existing AWS Network Load Balancer
description:
  - Enables new Availability Zones on an existing Network Load Balancer with C(SetSubnets),
    without recreating it, so its DNS name and existing IP addresses are kept.
  - Only adds subnets for Availability Zones that are not yet enabled on the load balancer.
    Subnets of already enabled zones are never replaced, and zones are never removed.
  - Does nothing if the load balancer does not exist. Use C(community.aws.elb_network_lb) to create it
    with the returned I(subnets).
options:
  name:
    description:
      - Name of the Network Load Balancer.
    required: true
    type: str
  subnets:
    description:
      - Subnet IDs that the load balancer should be enabled in, one per Availability Zone.
    required: true
    type: list
    elements: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Enable the zones of all cluster subnets on an existing NLB
  vitabaks.autobase.aws_nlb_subnets:
    name: postgres-cluster-primary
    subnets:
      - subnet-0a1b2c3d4e5f60001
      - subnet-0a1b2c3d4e5f60002
      - subnet-0a1b2c3d4e5f60003
    region: us-west-2
"""

RETURN = r"""
subnets:
  description:
    - Subnet IDs of the load balancer after the change, or the requested I(subnets) if it does not exist.
    - Pass them to C(community.aws.elb_network_lb), so that it does not try to modify the subnets.
  returned: always
  type: list
  elements: str
"""

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def describe_load_balancer(module, client, name):
    try:
        return client.describe_load_balancers(Names=[name])["LoadBalancers"][0]
    except is_boto3_error_code("LoadBalancerNotFound"):
        return None
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to describe load balancer '{0}'".format(name))


def describe_subnet_zones(module, client, subnet_ids):
    try:
        subnets = client.describe_subnets(SubnetIds=subnet_ids)["Subnets"]
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to describe subnets")
    return dict((subnet["SubnetId"], subnet["AvailabilityZone"]) for subnet in subnets)


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            subnets=dict(type="list", elements="str", required=True),
        ),
        supports_check_mode=True,
    )

    name = module.params["name"]
    elbv2 = module.client("elbv2")

    load_balancer = describe_load_balancer(module, elbv2, name)
    if load_balancer is None:
        module.exit_json(changed=False, subnets=module.params["subnets"])
    if load_balancer["Type"] != "network":
        module.fail_json(msg="Load balancer '{0}' is not a Network Load Balancer.".format(name))

    current_zones = load_balancer["AvailabilityZones"]
    current_subnets = [zone["SubnetId"] for zone in current_zones]
    enabled_zones = set(zone["ZoneName"] for zone in current_zones)

    subnet_zones = describe_subnet_zones(module, module.client("ec2"), module.params["subnets"])
    added_subnets = []
    for subnet_id in module.params["subnets"]:
        zone = subnet_zones[subnet_id]
        if zone in enabled_zones:
            continue
        added_subnets.append(subnet_id)
        enabled_zones.add(zone)

    subnets = current_subnets + added_subnets
    if not added_subnets:
        module.exit_json(changed=False, subnets=subnets)
    if module.check_mode:
        module.exit_json(changed=True, subnets=subnets)

    # SetSubnets requires the full list of subnets, including the subnets of already enabled zones.
    try:
        elbv2.set_subnets(LoadBalancerArn=load_balancer["LoadBalancerArn"], Subnets=subnets)
        elbv2.get_waiter("load_balancer_available").wait(LoadBalancerArns=[load_balancer["LoadBalancerArn"]])
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to add subnets to load balancer '{0}'".format(name))

    module.exit_json(changed=True, subnets=subnets)


if __name__ == "__main__":
    main()
