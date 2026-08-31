
--1

CREATE EXTERNAL TABLE `ljgm_zoomcamp.yellow_taxi_2024-01-06_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://ljgm-de-zoomcamp-landing/yellow_tripdata_2024-*.parquet']
);


--2
CREATE OR REPLACE TABLE `ljgm_zoomcamp.yellow_taxi_2024-01-06`
AS
SELECT *
FROM `ljgm_zoomcamp.yellow_taxi_2024-01-06_external`;


select distinct(PULocationID) from `ljgm_zoomcamp.yellow_taxi_2024-01-06_external`;


 select distinct(PULocationID) from  `ljgm_zoomcamp.yellow_taxi_2024-01-06`;


 --3

 select PULocationID from `ljgm_zoomcamp.yellow_taxi_2024-01-06`;

 select PULocationID, DOLocationID from `ljgm_zoomcamp.yellow_taxi_2024-01-06`;



 --4


 select count(1) from `ljgm_zoomcamp.yellow_taxi_2024-01-06_external` where  fare_amount = 0;


--5.-

CREATE OR REPLACE TABLE `ljgm_zoomcamp.yellow_taxi_2024-01-06_partitioned_clustered`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID AS
SELECT *
FROM `ljgm_zoomcamp.yellow_taxi_2024-01-06`;

 --6

 select distinct(VendorID) from `ljgm_zoomcamp.yellow_taxi_2024-01-06_partitioned_clustered`
WHERE tpep_dropoff_datetime >= TIMESTAMP '2024-03-01 00:00:00'
  AND tpep_dropoff_datetime <  TIMESTAMP '2024-03-16 00:00:00';


 select distinct(VendorID) from `ljgm_zoomcamp.yellow_taxi_2024-01-06`
 WHERE tpep_dropoff_datetime >= TIMESTAMP '2024-03-01 00:00:00'
  AND tpep_dropoff_datetime <  TIMESTAMP '2024-03-16 00:00:00';

