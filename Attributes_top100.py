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



import pandas as pd

# Load your CSV file (change path if needed)
df = pd.read_sql_table("top_100_men", con=engine)


# Define your final desired column order (💡 Fixed missing comma after 'Discount')
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

    # Skip the first "Watch Information" line
    if lines and lines[0].lower() == "watch information":
        lines = lines[1:]

    specs = {}
    i = 0
    while i < len(lines) - 1:
        key = lines[i].strip()
        key_lower = key.lower()

        # Stop parsing if warranty section starts (except 'Warranty Type')
        if "warranty" in key_lower and "warranty type" not in key_lower:
            break

        value = lines[i + 1].strip()
        specs[key] = value
        i += 2

    return specs

# Apply parsing to 'Specs' column
parsed_specs = df['specs'].apply(parse_specs)

# Build structured rows from parsed specs
structured_rows = []
for i, spec_dict in enumerate(parsed_specs):
    row_data = {}

    # Start with non-spec data
    for col in ["url", "brand", "product_name", "price", "imageurl", "ratings", "discount"]:
        row_data[col] = df.at[i, col] if col in df.columns else ""

    # Add spec-based fields
    for col in final_columns:
        if col not in row_data:
            row_data[col] = spec_dict.get(col, "")

    structured_rows.append(row_data)

# Create the final structured DataFrame
final_df = pd.DataFrame(structured_rows, columns=final_columns)

# Save the final output
final_df.to_sql("Final_Watch_Dataset_Men_output", con=engine, if_exists="replace", index=False)

# Load your CSV file (change path if needed)
df = pd.read_sql_table("top_100_women", con=engine)


# Define your final desired column order (💡 Fixed missing comma after 'Discount')
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

    # Skip the first "Watch Information" line
    if lines and lines[0].lower() == "watch information":
        lines = lines[1:]

    specs = {}
    i = 0
    while i < len(lines) - 1:
        key = lines[i].strip()
        key_lower = key.lower()

        # Stop parsing if warranty section starts (except 'Warranty Type')
        if "warranty" in key_lower and "warranty type" not in key_lower:
            break

        value = lines[i + 1].strip()
        specs[key] = value
        i += 2

    return specs

# Apply parsing to 'Specs' column
parsed_specs = df['specs'].apply(parse_specs)

# Mapping from raw dataframe column names to final schema column names
column_mapping = {
    "url": "URL",
    "brand": "Brand",
    "product_name": "Product Name",
    "model_number": "Model Number",  # optional if you already extracted it
    "price": "Price",
    "ratings": "Ratings",
    "discount": "Discount",
    "imageurl": "ImageURL"
}

# Build structured rows from parsed specs
structured_rows = []
for i, spec_dict in enumerate(parsed_specs):
    row_data = {}

    # Start with non-spec data using mapped column names
    for raw_col, final_col in column_mapping.items():
        row_data[final_col] = df.at[i, raw_col] if raw_col in df.columns else ""

    # Add spec-based fields (only if not already filled from above)
    for col in final_columns:
        if col not in row_data or not row_data[col]:
            row_data[col] = spec_dict.get(col, "")

    structured_rows.append(row_data)

# Create the final structured DataFrame
final_df = pd.DataFrame(structured_rows, columns=final_columns)

# Save the final output to Supabase
final_df.to_sql("Final_Watch_Dataset_Women_output", con=engine, if_exists="replace", index=False)
