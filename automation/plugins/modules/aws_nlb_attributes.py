#!/usr/bin/python
# -*- coding: utf-8 -*-

# Temporary workaround for attributes that community.aws.elb_network_lb does not support yet,
# such as dns_record.client_routing_policy (Availability Zone affinity).

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: aws_nlb_attributes
short_description: Set attributes of an existing AWS Network Load Balancer
description:
  - Sets the given attributes with C(ModifyLoadBalancerAttributes) when they differ from the current values.
    Attributes that are not listed are not changed.
options:
  name:
    description:
      - Name of the Network Load Balancer. It must already exist.
    required: true
    type: str
  attributes:
    description:
      - Attributes to set, as a dictionary of attribute keys and values.
      - Boolean values are converted to C(true) or C(false).
    required: true
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Enable Availability Zone affinity
  vitabaks.autobase.aws_nlb_attributes:
    name: postgres-cluster-replica
    attributes:
      dns_record.client_routing_policy: availability_zone_affinity
    region: us-west-2
"""

RETURN = r"""
attributes:
  description: The requested attributes with their values after the change.
  returned: always
  type: dict
"""

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def to_attribute_value(value):
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            attributes=dict(type="dict", required=True),
        ),
        supports_check_mode=True,
    )

    name = module.params["name"]
    desired = dict((key, to_attribute_value(value)) for key, value in module.params["attributes"].items())
    client = module.client("elbv2")

    try:
        load_balancer_arn = client.describe_load_balancers(Names=[name])["LoadBalancers"][0]["LoadBalancerArn"]
    except is_boto3_error_code("LoadBalancerNotFound"):
        module.fail_json(msg="Load balancer '{0}' does not exist.".format(name))
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to describe load balancer '{0}'".format(name))

    try:
        current = client.describe_load_balancer_attributes(LoadBalancerArn=load_balancer_arn)["Attributes"]
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to describe attributes of load balancer '{0}'".format(name))
    current = dict((attribute["Key"], attribute["Value"]) for attribute in current)

    changes = [{"Key": key, "Value": value} for key, value in desired.items() if current.get(key) != value]
    if not changes:
        module.exit_json(changed=False, attributes=desired)
    if module.check_mode:
        module.exit_json(changed=True, attributes=desired)

    try:
        client.modify_load_balancer_attributes(LoadBalancerArn=load_balancer_arn, Attributes=changes)
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to modify attributes of load balancer '{0}'".format(name))

    module.exit_json(changed=True, attributes=desired)


if __name__ == "__main__":
    main()
