SELECT tpep_pickup_datetime
FROM {{ source('raw_data', 'yellow_tripdata_partitioned_clustered') }}