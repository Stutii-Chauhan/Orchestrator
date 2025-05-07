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

    # Rename columns from snake_case or strange names to match final_df
    rename_map = {
        "url": "URL",
        "brand": "Brand",
        "model_number": "Model Number",
        "product_name": "Product Name",
        "ratings": "Ratings",
        "rating(out_of_5)": "Ratings",       # 👈 fix for actual Supabase column
        "price": "Price",
        "discount": "Discount",
        "discount_(%)": "Discount",         # 👈 fix for actual Supabase column
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

    filled_df.rename(columns=rename_map, inplace=True)

    # Merge original and filled datasets
    merged_df = final_df.merge(filled_df, on=key_col, how="left", suffixes=("", "_filled"))

    # For all columns in final_df, try to fill from *_filled
    for col in final_df.columns:
        filled_col = f"{col}_filled"
        if filled_col in merged_df.columns:
            merged_df[col] = merged_df[col].where(
                merged_df[col].notna() & (merged_df[col] != ""),
                merged_df[filled_col]
            )

    # Drop any *_filled columns
    merged_df.drop(columns=[col for col in merged_df.columns if col.endswith("_filled")], inplace=True)

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

    # ----------------------------
    # Normalize units consistently
    # ----------------------------
    def normalize_dimension(value):
        if pd.isna(value):
            return value

        val = str(value).strip().lower()

        # Convert from centimeters to millimeters
        if "centimeter" in val:
            num = re.findall(r"[\d\.]+", val)
            if num:
                mm_value = float(num[0]) * 10
                return f"{int(mm_value) if mm_value.is_integer() else mm_value} Millimeters"

        # Convert millimeter/millimetre to 'Millimeters'
        if "millimeter" in val or "millimetre" in val:
            num = re.findall(r"[\d\.]+", val)
            if num:
                return f"{num[0]} Millimeters"

        # If just numeric value
        if val.replace('.', '', 1).isdigit():
            return f"{val} Millimeters"

        return value

    # Apply to dimension columns
    for col in ["Band Width", "Case Diameter", "Case Thickness"]:
        final_df[col] = final_df[col].apply(normalize_dimension)

    # Upload final result
    final_df.to_sql(output_table, con=engine, if_exists="replace", index=False)


# -------------------------------------
# Run for Men and Women
# -------------------------------------
if __name__ == "__main__":
    process_watch_table(
        source_table="top_100_men",
        filled_table="top100_men_filled",
        output_table="Final_Watch_Dataset_Men_output"
    )

    process_watch_table(
        source_table="top_100_women",
        filled_table="top100_women_filled",
        output_table="Final_Watch_Dataset_Women_output"
    )


