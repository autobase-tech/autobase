#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: aws_secret_value
short_description: Update only the value of an existing AWS Secrets Manager secret
description:
  - Writes a new secret value with C(PutSecretValue) when it differs from the current value,
    or on every run when I(compare=false).
  - The secret must already exist. The module never creates or deletes secrets and never changes
    their description, KMS key, resource policy, rotation, replication, or tags.
  - JSON values are compared as parsed data, so formatting differences do not trigger an update.
options:
  name:
    description:
      - Name or ARN of the secret.
    required: true
    type: str
  secret:
    description:
      - Secret value to store.
      - Mutually exclusive with I(json_secret).
    type: str
  json_secret:
    description:
      - Secret value to store as JSON.
      - Mutually exclusive with I(secret).
    type: json
  secret_type:
    description:
      - Store the value in C(SecretString) or C(SecretBinary).
    choices: ['string', 'binary']
    default: string
    type: str
  overwrite:
    description:
      - Replace the current value when it differs.
      - When C(false), the value is written only if the secret has no current value.
    default: true
    type: bool
  compare:
    description:
      - Read the current value with C(GetSecretValue) and write only when it differs.
      - When C(false), C(GetSecretValue) is not called and the value is written on every run,
        so the task always reports a change. Use it where reading secret values is not permitted.
    default: true
    type: bool
  merge:
    description:
      - Apply I(json_secret) to the current JSON object as a JSON Merge Patch (RFC 7396)
        instead of replacing it. Nested objects are merged, and keys set to C(null) are removed.
      - Keys that are not in I(json_secret) are preserved.
      - Requires I(json_secret) and I(compare=true). Fails if the current value is not a JSON object.
    default: false
    type: bool
  replace_keys:
    description:
      - Top-level keys of I(json_secret) that replace the current values entirely instead of being merged.
      - Used only with I(merge=true).
    type: list
    elements: str
    default: []
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Update the value of a secret managed elsewhere
  vitabaks.autobase.aws_secret_value:
    name: autobase/postgres-cluster-01/postgresql/users/app_user
    json_secret:
      username: app_user
      password: "{{ app_user_password }}"
    region: us-west-2

- name: Add one user and remove another, keeping other keys of the secret
  vitabaks.autobase.aws_secret_value:
    name: backend/production/db
    json_secret:
      users:
        app_user: "{{ app_user_password }}"
        old_user: null
    merge: true
    region: us-west-2
"""

RETURN = r"""
secret:
  description: Secret identifiers. The secret value is never returned.
  returned: always
  type: dict
  contains:
    name:
      description: The secret name.
      type: str
    arn:
      description: The secret ARN.
      type: str
    version_id:
      description: The version ID of the new value. Present only when a value was written.
      type: str
"""

import json

from ansible.module_utils.common.text.converters import to_bytes

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def describe_secret(module, client, name):
    try:
        return client.describe_secret(SecretId=name)
    except is_boto3_error_code("ResourceNotFoundException"):
        module.fail_json(msg="Secret '{0}' does not exist. It must be created before its value can be updated.".format(name))
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to describe secret '{0}'".format(name))


def get_current_value(module, client, name):
    """Returns the AWSCURRENT version, or None when the secret has no value yet."""
    try:
        return client.get_secret_value(SecretId=name)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to read the value of secret '{0}'".format(name))


def merge_patch(target, patch):
    """Applies a JSON Merge Patch (RFC 7396)."""
    if not isinstance(patch, dict):
        return patch
    result = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def values_match(current, desired, secret_type, is_json):
    if current is None:
        return False
    if secret_type == "SecretBinary":
        return current.get("SecretBinary") == to_bytes(desired)
    current_value = current.get("SecretString")
    if current_value is None:
        return False
    if is_json:
        try:
            return json.loads(current_value) == json.loads(desired)
        except ValueError:
            return False
    return current_value == desired


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            secret=dict(type="str", no_log=True),
            json_secret=dict(type="json", no_log=True),
            secret_type=dict(type="str", choices=["string", "binary"], default="string"),
            overwrite=dict(type="bool", default=True),
            compare=dict(type="bool", default=True),
            merge=dict(type="bool", default=False),
            replace_keys=dict(type="list", elements="str", default=[], no_log=False),
        ),
        mutually_exclusive=[["secret", "json_secret"]],
        required_one_of=[["secret", "json_secret"]],
        supports_check_mode=True,
    )

    name = module.params["name"]
    is_json = module.params["json_secret"] is not None
    desired = module.params["json_secret"] if is_json else module.params["secret"]
    secret_type = "SecretBinary" if module.params["secret_type"] == "binary" else "SecretString"
    merge = module.params["merge"]

    if merge and (not is_json or secret_type != "SecretString"):
        module.fail_json(msg="merge requires json_secret and secret_type string.")
    if merge and not module.params["compare"]:
        module.fail_json(msg="merge requires compare, because the current value must be read to be merged.")

    client = module.client("secretsmanager")

    secret = describe_secret(module, client, name)
    if secret.get("DeletedDate"):
        module.fail_json(msg="Secret '{0}' is scheduled for deletion. Restore it before updating its value.".format(name))

    result = {"name": secret["Name"], "arn": secret["ARN"]}

    # DescribeSecret shows whether a current value exists without reading it.
    has_value = any("AWSCURRENT" in stages for stages in (secret.get("VersionIdsToStages") or {}).values())
    if has_value and not module.params["overwrite"]:
        module.exit_json(changed=False, secret=result)

    current = None
    if has_value and module.params["compare"]:
        current = get_current_value(module, client, name)

    if merge:
        current_data = {}
        if current is not None:
            try:
                current_data = json.loads(current.get("SecretString") or "")
            except ValueError:
                current_data = None
            if not isinstance(current_data, dict):
                module.fail_json(msg="Secret '{0}' does not contain a JSON object, so the new value cannot be merged into it.".format(name))
        patch = json.loads(desired)
        if isinstance(patch, dict):
            for key in module.params["replace_keys"]:
                if key in patch:
                    current_data.pop(key, None)
        desired = json.dumps(merge_patch(current_data, patch))

    if values_match(current, desired, secret_type, is_json):
        module.exit_json(changed=False, secret=result)
    if module.check_mode:
        module.exit_json(changed=True, secret=result)

    put_args = {"SecretId": name}
    put_args[secret_type] = to_bytes(desired) if secret_type == "SecretBinary" else desired
    try:
        response = client.put_secret_value(**put_args)
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json_aws(e, msg="Failed to update the value of secret '{0}'".format(name))

    result["version_id"] = response.get("VersionId")
    module.exit_json(changed=True, secret=result)


if __name__ == "__main__":
    main()
