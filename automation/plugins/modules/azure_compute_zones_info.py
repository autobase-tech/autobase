#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: azure_compute_zones_info
short_description: Discover Azure VM availability zones and subscription restrictions
description:
  - Lists regional availability zones and the zones supporting a VM SKU in this subscription.
  - Uses the Azure SDK and the same credentials as C(azure.azcollection), without Azure CLI.
  - Requires C(Microsoft.Resources/subscriptions/locations/read) and C(Microsoft.Compute/skus/read).
options:
  location:
    description: Azure region name.
    required: true
    type: str
  vm_size:
    description: VM SKU to check.
    required: true
    type: str
extends_documentation_fragment:
  - azure.azcollection.azure
"""

EXAMPLES = r"""
- name: Discover zones for the requested Azure VM SKU
  vitabaks.autobase.azure_compute_zones_info:
    location: westeurope
    vm_size: Standard_D4s_v5
"""

RETURN = r"""
region_zones:
  description: All logical availability zones of the region, sorted by name.
  returned: always
  type: list
  elements: str
zones:
  description: Zones in which the requested SKU is offered, including restricted zones.
  returned: always
  type: list
  elements: str
zones_available:
  description: SKU zones remaining after applying subscription restrictions.
  returned: always
  type: list
  elements: str
regional_available:
  description: Whether the SKU can be deployed regionally in this subscription.
  returned: always
  type: bool
"""

from ansible_collections.azure.azcollection.plugins.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.compute import ComputeManagementClient
except ImportError:
    # AzureRMModuleBase reports missing SDK dependencies.
    pass


def normalize_location(location):
    return location.replace(" ", "").lower()


def sku_zones(sku, location):
    """Separate an unsupported zonal SKU from subscription restrictions on its zones."""
    location = normalize_location(location)
    zones = set()
    for info in sku.get("location_info") or []:
        if normalize_location(info["location"]) == location:
            zones.update(str(zone) for zone in info.get("zones") or [])

    regional_available = True
    restricted_zones = set()
    for restriction in sku.get("restrictions") or []:
        info = restriction.get("restriction_info") or {}
        locations = info.get("locations") or restriction.get("values") or []
        if locations and location not in [normalize_location(value) for value in locations]:
            continue
        if restriction.get("type", "").lower() == "location":
            regional_available = False
        elif restriction.get("type", "").lower() == "zone":
            restricted_zones.update(str(zone) for zone in info.get("zones") or [])

    return dict(
        zones=sorted(zones),
        zones_available=sorted(zones - restricted_zones) if regional_available else [],
        regional_available=regional_available,
    )


class AzureComputeZonesInfo(AzureRMModuleBase):
    def __init__(self):
        super(AzureComputeZonesInfo, self).__init__(
            dict(location=dict(type="str", required=True), vm_size=dict(type="str", required=True)),
            supports_check_mode=True, supports_tags=False, facts_module=True,
        )

    def exec_module(self, location, vm_size, **kwargs):
        location = normalize_location(location)
        try:
            # Iterating the SDK pagers follows all nextLink pages.
            locations = self.subscription_client.subscriptions.list_locations(self.subscription_id)
            region = next((item for item in locations if normalize_location(item.name) == location), None)
            if region is None:
                self.fail("Azure region '{0}' was not found in this subscription.".format(location))
            region_zones = sorted(str(item.logical_zone) for item in region.availability_zone_mappings or [])
            client = self.get_mgmt_svc_client(
                ComputeManagementClient, base_url=self._cloud_environment.endpoints.resource_manager,
                api_version="2021-07-01",
            )
            skus = client.resource_skus.list(filter="location eq '{0}'".format(location))
            sku = next((item.as_dict() for item in skus
                        if item.resource_type == "virtualMachines" and item.name.lower() == vm_size.lower()
                        and location in [normalize_location(value) for value in item.locations or []]), None)
            if sku is None:
                self.fail("VM SKU '{0}' is not offered in Azure region '{1}'.".format(vm_size, location))
        except Exception as exc:
            self.fail("Failed to discover Azure zones for '{0}' in '{1}': {2}".format(vm_size, location, exc))
        return dict(changed=False, region_zones=region_zones, **sku_zones(sku, location))


def main():
    AzureComputeZonesInfo()


if __name__ == "__main__":
    main()
