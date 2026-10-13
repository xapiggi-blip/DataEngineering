/* @bruin
name: staging.trips
type: duckdb.sql

depends:
  - ingestion.trips
  - ingestion.payment_lookup

materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_datetime
  time_granularity: timestamp

columns:
  - name: pickup_datetime
    type: timestamp
    primary_key: true
    checks:
      - name: not_null

custom_checks:
  - name: row_count_greater_than_zero
    query: |
      SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
      FROM staging.trips
    value: 1
@bruin */

WITH normalized AS (
    SELECT
        TRY_CAST(CASE
            WHEN t.taxi_type = 'green' THEN t.lpep_pickup_datetime
            ELSE t.tpep_pickup_datetime
        END AS TIMESTAMP) AS pickup_datetime,
        TRY_CAST(CASE
            WHEN t.taxi_type = 'green' THEN t.lpep_dropoff_datetime
            ELSE t.tpep_dropoff_datetime
        END AS TIMESTAMP) AS dropoff_datetime,
        TRY_CAST(t.pu_location_id AS BIGINT) AS pickup_location_id,
        TRY_CAST(t.do_location_id AS BIGINT) AS dropoff_location_id,
        TRY_CAST(t.fare_amount AS DOUBLE) AS fare_amount,
        t.taxi_type,
        t.payment_type,
        t.extracted_at
    FROM ingestion.trips AS t
    WHERE TRY_CAST(CASE
        WHEN t.taxi_type = 'green' THEN t.lpep_pickup_datetime
        ELSE t.tpep_pickup_datetime
    END AS TIMESTAMP) >= TRY_CAST('{{ start_datetime }}' AS TIMESTAMP)
      AND TRY_CAST(CASE
        WHEN t.taxi_type = 'green' THEN t.lpep_pickup_datetime
        ELSE t.tpep_pickup_datetime
    END AS TIMESTAMP) < TRY_CAST('{{ end_datetime }}' AS TIMESTAMP)
)
SELECT
    n.pickup_datetime,
    n.dropoff_datetime,
    n.pickup_location_id,
    n.dropoff_location_id,
    n.fare_amount,
    n.taxi_type,
    p.payment_type_name
FROM normalized AS n
LEFT JOIN ingestion.payment_lookup AS p
    ON TRY_CAST(n.payment_type AS INTEGER) = p.payment_type_id
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY
        n.pickup_datetime,
        n.dropoff_datetime,
        n.pickup_location_id,
        n.dropoff_location_id,
        n.fare_amount,
        n.taxi_type
    ORDER BY n.extracted_at
) = 1
