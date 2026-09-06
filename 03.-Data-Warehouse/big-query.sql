
-- Check yellow trip data
SELECT * FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_2019_10_ext` limit 10;

-- Create a non partitioned table from external table
CREATE OR REPLACE TABLE `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_non_partitioned` AS
SELECT * FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_2019_10_ext` ;


-- Create a partitioned table from external table
CREATE OR REPLACE TABLE `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_partitioned`
PARTITION BY
  DATE(tpep_pickup_datetime) AS
SELECT * FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_2019_10_ext`;

-- Impact of partition
-- Scanning 75.54 MB of data
SELECT DISTINCT(VendorID)
FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_non_partitioned`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31';

-- Scanning ~0 MB of DATA
SELECT DISTINCT(VendorID)
FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_partitioned` 
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31';

-- Let's look into the partitions
SELECT table_name, partition_id, total_rows
FROM `nytaxi.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_tripdata_partitioned'
ORDER BY total_rows DESC;

-- Creating a partition and cluster table
CREATE OR REPLACE TABLE `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_partitioned_clustered`
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID AS
SELECT * FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_2019_10_ext`;

-- Query scans 75.54 MB
SELECT count(*) as trips
FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_partitioned`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID='1';

-- Query scans 46.42 MB
SELECT count(*) as trips
FROM `kestra-sandbox-498900.ljgm_zoomcamp.yellow_tripdata_partitioned_clustered`
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID='1';

