#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm



dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


@click.command()
@click.option('--pg-user', default='root', show_default=True, help='PostgreSQL user')
@click.option('--pg-password', default='root', show_default=True, help='PostgreSQL password')
@click.option('--pg-host', default='localhost', show_default=True, help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, show_default=True, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', show_default=True, help='PostgreSQL database name')
@click.option('--year', default=2021, type=int, show_default=True, help='Data year')
@click.option('--month', default=1, type=int, show_default=True, help='Data month')
@click.option('--chunk-size', default=1000, type=int, show_default=True, help='CSV chunk size')
@click.option('--target-table', default='yellow_taxi_data', show_default=True, help='Target table name')
def run(
    pg_user,
    pg_password,
    pg_host,
    pg_port,
    pg_db,
    year,
    month,
    chunk_size,
    target_table,
):
    # Config
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
    file = f'yellow_tripdata_{year}-{month:02d}.csv.gz'

    # DB connection
    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}')

    # Create iterator
    df_iter = pd.read_csv(
        prefix + file,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunk_size
    )

    # Ingestion loop
    first = True

    for df_chunk in tqdm(df_iter, desc="Ingesting data"):

        if first:
            df_chunk.head(0).to_sql(
                name=target_table,
                con=engine,
                if_exists="replace"
            )
            first = False
            print("Table created")

        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists="append",
            chunksize=chunk_size,
            method="multi"
        )

        print("Inserted:", len(df_chunk))

if __name__ == "__main__":
    run() 