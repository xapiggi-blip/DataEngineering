import pandas as pd
from sqlalchemy import create_engine

# conexión
engine = create_engine("postgresql+psycopg://root:root@localhost:5432/ny_taxi")

# ---- CARGA PARQUET (viajes) ----
df_trips = pd.read_parquet("green_tripdata_2025-11.parquet")

df_trips.to_sql(
    "green_taxi_trips", 
    engine,
    if_exists="replace",
    index=False
)

# ---- CARGA CSV (zonas) ----
df_zones = pd.read_csv("taxi_zone_lookup.csv")

df_zones.to_sql(
    "zones",
    engine,
    if_exists="replace",
    index=False
)