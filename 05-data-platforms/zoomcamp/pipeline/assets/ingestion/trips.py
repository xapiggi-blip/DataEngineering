"""@bruin
name: ingestion.trips
type: python
image: python:3.11
connection: duckdb-default

materialization:
  type: table
  strategy: append

@bruin"""

import json
import os
import re
import time
from datetime import datetime
from typing import List, Tuple

import pandas as pd
import pyarrow as pa
from dateutil.relativedelta import relativedelta

#BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download"
CHUNK_SIZE = 50_000

# Union of the columns found in the Yellow and Green taxi CSV files.
# Keeping one ordered schema lets Bruin append every Arrow batch consistently.
SOURCE_COLUMNS = [
    "vendor_id",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "store_and_fwd_flag",
    "ratecode_id",
    "pu_location_id",
    "do_location_id",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "ehail_fee",
    "improvement_surcharge",
    "total_amount",
    "payment_type",
    "trip_type",
    "congestion_surcharge",
    "airport_fee",
]
OUTPUT_COLUMNS = SOURCE_COLUMNS + ["taxi_type", "extracted_at"]
ARROW_SCHEMA = pa.schema(
    [
        (column, pa.string())
        for column in OUTPUT_COLUMNS
        if column != "extracted_at"
    ]
    + [("extracted_at", pa.timestamp("us", tz="UTC"))]
)

SOURCE_COLUMN_ALIASES = {
    "vendorid": "vendor_id",
    "ratecodeid": "ratecode_id",
    "pulocationid": "pu_location_id",
    "dolocationid": "do_location_id",
}


def generate_months_to_ingest(
    start_date: str, end_date: str
) -> List[Tuple[int, int]]:
    """Devuelve todos los pares (año, mes) entre las fechas."""
    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    if start > end:
        raise ValueError("BRUIN_START_DATE debe ser anterior a BRUIN_END_DATE")

    current = start.replace(day=1)
    last = end.replace(day=1)
    months = []

    while current <= last:
        months.append((current.year, current.month))
        current += relativedelta(months=1)

    return months


def build_parquet_url(taxi_type: str, year: int, month: int) -> str:
    """Construye la URL del archivo mensual de NYC TLC."""
    return (
        #f"{BASE_URL}/{taxi_type}_tripdata_"
        #f"{year}-{month:02d}.parquet"
        f"{BASE_URL}/{taxi_type}/"
        f"{taxi_type}_tripdata_{year}-{month:02d}.csv.gz"
    )


def materialize():
    start_date = os.environ["BRUIN_START_DATE"]
    end_date = os.environ["BRUIN_END_DATE"]

    bruin_vars = json.loads(os.environ.get("BRUIN_VARS", "{}") or "{}")
    taxi_types = bruin_vars.get("taxi_types", ["yellow"])

    if isinstance(taxi_types, str):
        taxi_types = [taxi_types]

    months = generate_months_to_ingest(start_date, end_date)
    print(f"Months to ingest: {months}")

    for taxi_type in taxi_types:
        for year, month in months:
            url = build_parquet_url(taxi_type, year, month)
            print(f"Fetching: {url}")

            for attempt in range(1, 4):
                try:
                    chunks = pd.read_csv(
                        url,
                        compression="gzip",
                        chunksize=CHUNK_SIZE,
                        low_memory=False,
                    )
                    break
                except Exception as exc:
                    if attempt == 3:
                        raise RuntimeError(f"No se pudo leer {url}") from exc

                    delay = 2**attempt
                    print(
                        f"Download attempt {attempt} failed for {url}; "
                        f"retrying in {delay}s"
                    )
                    time.sleep(delay)

            try:
                for chunk in chunks:
                    normalized_names = {}
                    for column in chunk.columns:
                        lowered = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", column).lower()
                        normalized_names[column] = SOURCE_COLUMN_ALIASES.get(
                            lowered.replace("_", ""), lowered
                        )
                    chunk = chunk.rename(columns=normalized_names)

                    for column in SOURCE_COLUMNS:
                        if column not in chunk.columns:
                            chunk[column] = pd.NA

                    chunk = chunk[SOURCE_COLUMNS].copy()
                    for column in SOURCE_COLUMNS:
                        chunk[column] = chunk[column].astype("string")

                    chunk["taxi_type"] = taxi_type
                    chunk["extracted_at"] = pd.Timestamp.now(tz="UTC")
                    yield pa.Table.from_pandas(
                        chunk[OUTPUT_COLUMNS],
                        schema=ARROW_SCHEMA,
                        preserve_index=False,
                    )
            except Exception as exc:
                raise RuntimeError(f"No se pudo procesar {url}") from exc
