-- +goose Up

-- Azure VM prices: East US, Linux, pay-as-you-go, USD/hour (26 September 2026).
-- Source: https://prices.azure.com/api/retail/prices (Virtual Machines, eastus,
-- Consumption, Linux Dsv6/Esv6 meters); see also the Azure Linux VM pricing page.
-- Monthly estimates use 730 hours. Availability and prices vary by subscription and region.
delete from public.cloud_instances where cloud_provider = 'azure';

insert into public.cloud_instances
  (cloud_provider, instance_group, instance_name, cpu, ram, price_hourly, price_monthly, currency, updated_at, shared_cpu)
values
  ('azure', 'Small Size', 'Standard_D2s_v6', 2, 8, 0.101, 73.730, '$', '2026-09-26', false),
  ('azure', 'Small Size', 'Standard_E2s_v6', 2, 16, 0.132, 96.360, '$', '2026-09-26', false),
  ('azure', 'Small Size', 'Standard_D4s_v6', 4, 16, 0.202, 147.460, '$', '2026-09-26', false),
  ('azure', 'Small Size', 'Standard_E4s_v6', 4, 32, 0.265, 193.450, '$', '2026-09-26', false),
  ('azure', 'Small Size', 'Standard_D8s_v6', 8, 32, 0.403, 294.190, '$', '2026-09-26', false),
  ('azure', 'Small Size', 'Standard_E8s_v6', 8, 64, 0.529, 386.170, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_D16s_v6', 16, 64, 0.806, 588.380, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_E16s_v6', 16, 128, 1.058, 772.340, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_E20s_v6', 20, 160, 1.323, 965.790, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_D32s_v6', 32, 128, 1.613, 1177.490, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_E32s_v6', 32, 256, 2.117, 1545.410, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_D48s_v6', 48, 192, 2.419, 1765.870, '$', '2026-09-26', false),
  ('azure', 'Medium Size', 'Standard_E48s_v6', 48, 384, 3.175, 2317.750, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_D64s_v6', 64, 256, 3.226, 2354.980, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_E64s_v6', 64, 512, 4.234, 3090.820, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_D96s_v6', 96, 384, 4.838, 3531.740, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_E96s_v6', 96, 768, 6.350, 4635.500, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_D128s_v6', 128, 512, 6.451, 4709.230, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_E128s_v6', 128, 1024, 8.467, 6180.910, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_D192s_v6', 192, 768, 9.677, 7064.210, '$', '2026-09-26', false),
  ('azure', 'Large Size', 'Standard_E192is_v6', 192, 1832, 13.971, 10198.830, '$', '2026-09-26', false);

-- The UI estimates disk cost as requested GiB * price_monthly. Azure bills
-- Standard/Premium disks by the next capacity tier, so these per-GiB rates
-- represent the form's default 100-GiB disk (billed as a 128-GiB tier).
-- Standard HDD S10: $5.888/month; Standard SSD E10: $9.60/month;
-- Premium SSD P10: $19.71/month. Ultra capacity: $0.000164/GiB-hour * 730.
-- Operations for Standard disks and provisioned IOPS/throughput for Ultra
-- are billed separately and are not included in this capacity estimate.
-- Source: https://prices.azure.com/api/retail/prices (Storage, eastus, LRS).
update public.cloud_volumes as cv
set price_monthly = prices.price_monthly,
    updated_at = date '2026-09-26'
from (values
  ('Standard_LRS', 0.05888),
  ('StandardSSD_LRS', 0.09600),
  ('Premium_LRS', 0.19710),
  ('UltraSSD_LRS', 0.11972)
) as prices(volume_type, price_monthly)
where cv.cloud_provider = 'azure'
  and cv.volume_type = prices.volume_type;

-- +goose Down

update public.cloud_volumes as cv
set price_monthly = prices.price_monthly,
    updated_at = date '2024-05-15'
from (values
  ('Standard_LRS', 0.040),
  ('StandardSSD_LRS', 0.075),
  ('Premium_LRS', 0.132),
  ('UltraSSD_LRS', 0.120)
) as prices(volume_type, price_monthly)
where cv.cloud_provider = 'azure'
  and cv.volume_type = prices.volume_type;

delete from public.cloud_instances where cloud_provider = 'azure';

insert into public.cloud_instances
  (cloud_provider, instance_group, instance_name, cpu, ram, price_hourly, price_monthly, currency, updated_at, shared_cpu)
values
  ('azure', 'Small Size', 'Standard_B1ms', 1, 2, 0.021, 15.111, '$', '2024-05-15', true),
  ('azure', 'Small Size', 'Standard_B2s', 2, 4, 0.042, 30.368, '$', '2024-05-15', true),
  ('azure', 'Small Size', 'Standard_D2s_v5', 2, 8, 0.096, 70.080, '$', '2024-05-15', false),
  ('azure', 'Small Size', 'Standard_E2s_v5', 2, 16, 0.126, 91.980, '$', '2024-05-15', false),
  ('azure', 'Small Size', 'Standard_D4s_v5', 4, 16, 0.192, 140.160, '$', '2024-05-15', false),
  ('azure', 'Small Size', 'Standard_E4s_v5', 4, 32, 0.252, 183.960, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_D8s_v5', 8, 32, 0.384, 280.320, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_E8s_v5', 8, 64, 0.504, 367.920, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_D16s_v5', 16, 64, 0.768, 560.640, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_E16s_v5', 16, 128, 1.008, 735.840, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_D32s_v5', 32, 128, 1.536, 1121.280, '$', '2024-05-15', false),
  ('azure', 'Medium Size', 'Standard_E32s_v5', 32, 256, 2.016, 1471.680, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_D48s_v5', 48, 192, 2.304, 1681.920, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_E48s_v5', 48, 384, 3.024, 2207.520, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_D64s_v5', 64, 256, 3.072, 2242.560, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_E64s_v5', 64, 512, 4.032, 2943.360, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_D96s_v5', 96, 384, 4.608, 3363.840, '$', '2024-05-15', false),
  ('azure', 'Large Size', 'Standard_E96s_v5', 96, 672, 6.048, 4415.040, '$', '2024-05-15', false);
