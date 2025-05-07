import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

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

# -------------------------------------
# Final Column Order (includes parsed specs)
# -------------------------------------
final_columns = [
    "URL", "Brand", "Product Name", "Model Number", "Price", "Ratings", "Discount",
    "Band Colour", "Band Material", "Band Width", "Case Diameter",
    "Case Material", "Case Thickness", "Dial Colour", "Crystal Material",
    "Case Shape", "Movement", "Water Resistance Depth", "Special Features",
    "ImageURL"
]

# -------------------------------------
# Column mapping from DB to output
# -------------------------------------
column_mapping = {
    "url": "URL",
    "brand": "Brand",
    "product_name": "Product Name",
    "model_number": "Model Number",  # optional
    "price": "Price",
    "ratings": "Ratings",
    "discount": "Discount",
    "imageurl": "ImageURL"
}

# -------------------------------------
# Parse 'specs' field into dictionary
# -------------------------------------
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

# -------------------------------------
# Fill missing values from filled table
# -------------------------------------
def apply_fallback_specs(final_df: pd.DataFrame, filled_table_name: str, engine, key_col="URL") -> pd.DataFrame:
    filled_df = pd.read_sql_table(filled_table_name, con=engine)

    # Map lowercase underscore columns to Title Case
    rename_map = {
        "url": "URL",
        "brand": "Brand",
        "model_number": "Model Number",
        "product_name": "Product Name",
        "ratings": "Ratings",
        "price": "Price",
        "discount": "Discount",
        "band_colour": "Band Colour",
        "band_material": "Band Material",
        "band_width": "Band Width",
        "case_diameter": "Case Diameter",
        "case_material": "Case Material",
        "case_thickness": "Case Thickness",
        "dial_colour": "Dial Colour",
        "crystal_material": "Crystal Material",
        "case_shape": "Case Shape",
        "movement": "Movement",
        "water_resistance_depth": "Water Resistance Depth",
        "special_features": "Special Features",
        "imageurl": "ImageURL"
    }

    # Rename columns in the filled table
    filled_df.rename(columns=rename_map, inplace=True)

    # Merge based on URL
    merged_df = final_df.merge(filled_df, on=key_col, how="left", suffixes=("", "_filled"))

    # Columns to fill (exclude raw ones)
    raw_cols = ["URL", "Brand", "Product Name", "Model Number", "Price", "Ratings", "Discount", "ImageURL"]
    attributes_to_fill = [col for col in final_df.columns if col not in raw_cols]

    for col in attributes_to_fill:
        filled_col = f"{col}_filled"
        if filled_col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(merged_df[filled_col])
            merged_df[col] = merged_df[col].replace("", merged_df[filled_col])

    merged_df.drop(columns=[f"{col}_filled" for col in attributes_to_fill if f"{col}_filled" in merged_df.columns], inplace=True)

    return merged_df


# -------------------------------------
# Processing Function
# -------------------------------------
def process_watch_table(source_table: str, filled_table: str, output_table: str):
    df = pd.read_sql_table(source_table, con=engine)
    parsed_specs = df['specs'].apply(parse_specs)

    structured_rows = []
    for i, spec_dict in enumerate(parsed_specs):
        row_data = {}

        # Add base info (non-specs)
        for raw_col, final_col in column_mapping.items():
            row_data[final_col] = df.at[i, raw_col] if raw_col in df.columns else ""

        # Add spec-based fields
        for col in final_columns:
            if col not in row_data or not row_data[col]:
                row_data[col] = spec_dict.get(col, "")

        structured_rows.append(row_data)

    # Create final DataFrame
    final_df = pd.DataFrame(structured_rows, columns=final_columns)

    # Fill missing specs from fallback table
    final_df = apply_fallback_specs(final_df, filled_table, engine)

    # Upload final result
    final_df.to_sql(output_table, con=engine, if_exists="replace", index=False)

# -------------------------------------
# Run for Men and Women
# -------------------------------------
process_watch_table("top_100_men", "top_100_men_filled", "Final_Watch_Dataset_Men_output")
process_watch_table("top_100_women", "top_100_women_filled", "Final_Watch_Dataset_Women_output")
