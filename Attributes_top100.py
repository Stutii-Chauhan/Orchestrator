import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import re

# -------------------------------------
# DB Setup
# -------------------------------------
db = os.environ["SUPABASE_DB"]
user = os.environ["SUPABASE_USER"]
raw_password = os.environ["SUPABASE_PASSWORD"]
host = os.environ["SUPABASE_HOST"]
port = os.environ["SUPABASE_PORT"]
password = quote_plus(raw_password)

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

# Load your CSV file (change path if needed)
df = pd.read_sql_table("top_100_men", con=engine)


# Define your final desired column order
final_columns = [
    "URL", "Brand", "Product Name", "Model Number", "Price", "Ratings", "Discount",
    "Band Colour", "Band Material", "Band Width", "Case Diameter",
    "Case Material", "Case Thickness", "Dial Colour", "Crystal Material",
    "Case Shape", "Movement", "Water Resistance Depth", "Special Features",
    "ImageURL"
]

# Function to parse the 'Specs' column into key-value pairs
def parse_specs(spec_str):
    if pd.isna(spec_str):
        return {}
    lines = [line.strip() for line in spec_str.strip().splitlines() if line.strip()]
    if lines and lines[0].lower() == "watch information":
        lines = lines[1:]
    specs = {}
    i = 0
    while i < len(lines) - 1:
        key = lines[i].strip()
        key_lower = key.lower()
        if "warranty" in key_lower and "warranty type" not in key_lower:
            break
        value = lines[i + 1].strip()
        specs[key] = value
        i += 2
    return specs

# Apply parsing to 'Specs' column
parsed_specs = df['specs'].apply(parse_specs)

# Map raw DB column names to final schema
column_mapping = {
    "url": "URL",
    "brand": "Brand",
    "product_name": "Product Name",
    "model_number": "Model Number",  # Leave blank if not in df
    "price": "Price",
    "ratings": "Ratings",
    "discount": "Discount",
    "imageurl": "ImageURL"
}

# Build structured rows
structured_rows = []
for i, spec_dict in enumerate(parsed_specs):
    row_data = {}

    # Add non-spec columns using mapping
    for raw_col, final_col in column_mapping.items():
        row_data[final_col] = df.at[i, raw_col] if raw_col in df.columns else ""

    # Add spec-based fields (only if not already filled)
    for col in final_columns:
        if col not in row_data or not row_data[col]:
            row_data[col] = spec_dict.get(col, "")

    structured_rows.append(row_data)

# Save the structured Men's output
final_df = pd.DataFrame(structured_rows, columns=final_columns)
final_df.to_sql("Final_Watch_Dataset_Men_output", con=engine, if_exists="replace", index=False)

# -----------------------------
# Process Women Dataset
# -----------------------------
df = pd.read_sql_table("top_100_women", con=engine)
parsed_specs = df['specs'].apply(parse_specs)

# Reuse same column mapping and final column list
structured_rows = []
for i, spec_dict in enumerate(parsed_specs):
    row_data = {}

    # Non-spec data
    for raw_col, final_col in column_mapping.items():
        row_data[final_col] = df.at[i, raw_col] if raw_col in df.columns else ""

    # Spec-based fields
    for col in final_columns:
        if col not in row_data or not row_data[col]:
            row_data[col] = spec_dict.get(col, "")

    structured_rows.append(row_data)

# Save the structured Women's output
final_df = pd.DataFrame(structured_rows, columns=final_columns)
final_df.to_sql("Final_Watch_Dataset_Women_output", con=engine, if_exists="replace", index=False)
