import { describe, expect, it } from 'vitest';
import { getDefaultCloudRegionSelection } from './defaultCloudRegion.ts';

describe('getDefaultCloudRegionSelection', () => {
  it.each([
    ['aws', 'us-east-1'],
    ['gcp', 'us-east1'],
    ['azure', 'eastus'],
    ['digitalocean', 'nyc1'],
    ['hetzner', 'ash'],
  ])('selects the preferred region for %s when available', (providerCode, datacenterCode) => {
    const preferredDatacenter = { code: datacenterCode, cloud_image: { image: { server_image: 'preferred' } } };
    const provider = {
      code: providerCode,
      cloud_regions: [
        { code: 'Europe', datacenters: [{ code: 'eu-west' }] },
        { code: 'North America', datacenters: [{ code: 'other-us' }, preferredDatacenter] },
      ],
    };

    expect(getDefaultCloudRegionSelection(provider)).toEqual({ regionCode: 'North America', datacenter: preferredDatacenter });
  });

  it('keeps the first available region when the preferred region is absent', () => {
    const datacenter = { code: 'eu-west' };
    const provider = {
      code: 'aws',
      cloud_regions: [
        { code: 'Europe', datacenters: [datacenter] },
        { code: 'North America', datacenters: [{ code: 'us-west-1' }] },
      ],
    };

    expect(getDefaultCloudRegionSelection(provider)).toEqual({ regionCode: 'Europe', datacenter });
  });

  it('keeps the first region for providers without a preferred region', () => {
    const datacenter = { code: 'other-region' };
    expect(getDefaultCloudRegionSelection({
      code: 'unknown',
      cloud_regions: [{ code: 'North America', datacenters: [datacenter] }],
    })).toEqual({ regionCode: 'North America', datacenter });
  });
});
