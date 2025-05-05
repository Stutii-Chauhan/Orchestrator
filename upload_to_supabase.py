import os
import pandas as pd
from sqlalchemy import create_engine

db = os.environ["SUPABASE_DB"]
user = os.environ["SUPABASE_USER"]
password = os.environ["SUPABASE_PASSWORD"]
host = os.environ["SUPABASE_HOST"]
port = os.environ["SUPABASE_PORT"]

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

for file in os.listdir("."):
    if file.endswith(".xlsx") or file.endswith(".csv"):
        if file.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        table_name = file.lower().replace(".xlsx", "").replace(".csv", "").replace(" ", "_")
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f" Uploaded: {table_name}")

#fixed some host name
#still didn't work
