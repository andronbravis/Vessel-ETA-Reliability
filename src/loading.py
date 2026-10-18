import os
import pandas as pd
from dotenv import load_dotenv
import psycopg

load_dotenv()

def load_ais(df_ais: pd.DataFrame):
    with psycopg.connect(dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
       password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT')) as conn:

        with conn.cursor() as cur:
            cur.execute("""
               CREATE TABLE IF NOT EXISTS vessel_eta(
                  Observation_id BIGINT GENERATED ALWAYS AS IDENTITY,
                  MMSI  VARCHAR(9) NOT NULL,
                  Name  TEXT,
                  Ship_Type TEXT NOT NULL,
                  Mobile_Type TEXT,
                  Destination TEXT NOT NULL,
                  Timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                  ETA TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                  Latitude DOUBLE PRECISION NOT NULL,
                  Longitude DOUBLE PRECISION NOT NULL,
                  Navigational_Status TEXT,
                  SOG DOUBLE PRECISION NOT NULL,
                  Mapped_LOCODE VARCHAR(5),
                  Class TEXT,
                  Dest_lat DOUBLE PRECISION,
                  Dest_lon DOUBLE PRECISION,
                  PRIMARY KEY(Observation_id)
               )
            """)

            cur.execute("TRUNCATE TABLE vessel_eta RESTART IDENTITY")

            with cur.copy("""
               COPY vessel_eta (Timestamp, Mobile_Type, MMSI, 
                  Latitude, Longitude, Navigational_Status, SOG,
                  Name, Ship_Type, Destination, ETA, Mapped_LOCODE,
                  Class, Dest_lat, Dest_lon) 
                  FROM STDIN WITH (FORMAT CSV)
            """) as copy:
                chunk = 500_000
                for i in range(0, df_ais.shape[0], chunk):
                    loaded = df_ais.iloc[i: i + chunk].to_csv(index=False, header=False)
                    copy.write(loaded)
        