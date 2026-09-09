select tpep_pickup_datetime
from {{}source('raw_data', 'yellow_tripdata_partitioned_clustered')}
