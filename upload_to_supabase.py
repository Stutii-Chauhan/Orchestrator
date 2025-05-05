import os
import pandas as pd
from sqlalchemy import create_engine

# Load Supabase DB credentials from environment
db = os.environ["SUPABASE_DB"]
user = os.environ["SUPABASE_USER"]
password = os.environ["SUPABASE_PASSWORD"]
host = os.environ["SUPABASE_HOST"]
port = os.environ["SUPABASE_PORT"]

# Optional Debug - GitHub will mask secrets in logs
print("🔍 DEBUGGING ENVIRONMENT VARIABLES")
print("HOST:", host)
print("USER:", user)
print("DB:", db)

# SQLAlchemy engine
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

# Loop over all data files in the repo root
for file in os.listdir("."):
    if file.endswith(".xlsx") or file.endswith(".csv"):
        print(f"📄 Processing: {file}")
        try:
            if file.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)

            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            table_name = file.lower().replace(".xlsx", "").replace(".csv", "").replace(" ", "_")
            
            # Upload to Supabase
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            print(f"✅ Uploaded: {table_name}")
        except Exception as e:
            print(f"❌ Failed to upload {file}: {e}")
