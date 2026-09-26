import { PROVIDERS } from '@shared/config/constants.ts';

const DEFAULT_REGION_CODES: Record<string, string> = {
  [PROVIDERS.AWS]: 'us-east-1',
  [PROVIDERS.GCP]: 'us-east1',
  [PROVIDERS.AZURE]: 'eastus',
  [PROVIDERS.DIGITAL_OCEAN]: 'nyc1',
  [PROVIDERS.HETZNER]: 'ash',
};

type Datacenter = { code?: string };
type CloudRegion<T extends Datacenter> = { code?: string; datacenters?: T[] | null };
type CloudProvider<T extends Datacenter> = { code?: string; cloud_regions?: CloudRegion<T>[] | null };

export const getDefaultCloudRegionSelection = <T extends Datacenter>(provider?: CloudProvider<T>) => {
  const preferredCode = provider?.code ? DEFAULT_REGION_CODES[provider.code] : undefined;
  const regions = provider?.cloud_regions;
  const region = (preferredCode
    ? regions?.find((item) => item.datacenters?.some((datacenter) => datacenter.code === preferredCode))
    : undefined) ?? regions?.[0];
  const datacenter = (preferredCode
    ? region?.datacenters?.find((item) => item.code === preferredCode)
    : undefined) ?? region?.datacenters?.[0];

  return { regionCode: region?.code, datacenter };
};
