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

#df_cleaned = pd.read_sql_table("product_price_cleaned", con=engine)

# PART 1: Product Code Extraction
# -----------------------------

# List of unwanted prefixes to remove (all in lowercase with trailing hyphen)
UNWANTED_PREFIXES = [
    "watch-",
    "women-",
    "men-",
    "strap-",
    "collection-",
    "couple-"
]

# (Measurement units defined for reference; not used directly here)
MEASUREMENT_UNITS = {"MM","CM","IN","mm", "cm", "in"}

def clean_token(token):
    """
    Cleans the candidate token by:
      1. Removing any unwanted prefixes (e.g. "watch-", "men-", etc.)
      2. If the token contains a dash, checking if the final segment is a measurement (like "22mm")
         and removing it.
    Returns the cleaned token.
    """
    token_clean = token
    # Remove unwanted prefixes.
    for prefix in UNWANTED_PREFIXES:
        if token_clean.lower().startswith(prefix):
            token_clean = token_clean[len(prefix):]

    # If the token contains a dash, check if the final segment is a measurement.
    if '-' in token_clean:
        parts = token_clean.split('-')
        last_part = parts[-1].lower()
        # If the final part matches digits + measurement (e.g. "22mm"), remove it.
        if re.fullmatch(r'\d+\s*(mm|cm|in)', last_part):
            token_clean = "-".join(parts[:-1])
    return token_clean

def extract_product_code(product_name):
    """
    Extracts a product code from the product_name.
    Steps:
      1. Tokenize the product_name with a regex that captures letters, digits, underscores, dashes, slashes, and periods.
      2. Keep tokens that either (a) contain both letters and digits, or (b) are all digits and at least 4 characters long.
      3. For tokens containing underscores or slashes, split them further.
      4. Choose the candidate token that appears nearest to the end of the product_name.
      5. Clean the token (remove unwanted prefixes and measurement segments).
      6. Convert the final result to UPPER-CASE.
    """
    if pd.isna(product_name):
        return None

    # Regex includes period to capture codes like "CDL.0006"
    tokens = re.findall(r'\b[\w\.\-\/]+\b', product_name)

    candidate_tokens = []
    for token in tokens:
        # Accept tokens that are all digits and at least 4 characters
        if token.isdigit():
            if len(token) >= 4:
                candidate_tokens.append(token)
        else:
            # Otherwise require that token contains both letters and digits.
            if re.search(r'[A-Za-z]', token) and re.search(r'\d', token):
                candidate_tokens.append(token)

    if not candidate_tokens:
        return None

    # Further split tokens containing underscores or slashes.
    refined_candidates = []
    for token in candidate_tokens:
        if '_' in token:
            refined_candidates.extend(token.split('_'))
        elif '/' in token:
            refined_candidates.extend(token.split('/'))
        else:
            refined_candidates.append(token)

    # Re-filter the refined candidates with the same criteria.
    final_candidates = []
    for token in refined_candidates:
        if token.isdigit():
            if len(token) >= 4:
                final_candidates.append(token)
        else:
            if re.search(r'[A-Za-z]', token) and re.search(r'\d', token):
                final_candidates.append(token)

    if not final_candidates:
        return None

    # Choose the candidate that appears nearest to the end of the product_name.
    last_candidate_uncleaned = None
    last_index = -1
    for token in final_candidates:
        index = product_name.rfind(token)
        if index > last_index:
            last_index = index
            last_candidate_uncleaned = token

    final_token = clean_token(last_candidate_uncleaned)

    return final_token.upper() if final_token else None

# -----------------------------
# PART 3: Apply to Dataset and Save
# -----------------------------

# Read the Excel file.

df_men = pd.read_sql_table("top_100_men_excel", con=engine)

# Drop rows where either "product_name" or "price" is null.
df_men = df_men.dropna(subset=["product_name", "price"])

# Update the DataFrame with extracted Product Code and Brand.
df_men["product_code"] = df_men["product_name"].apply(extract_product_code)


# -----------------------------
# PART 3: Apply to Dataset and Save
# -----------------------------

# Read the Excel file.
df_women = pd.read_sql_table("top_100_women_excel", con=engine)


# Drop rows where either "product_name" or "price" is null.
df_women = df_women.dropna(subset=["product_name", "price"])

# Update the DataFrame with extracted Product Code and Brand.
df_women["product_code"] = df_women["product_name"].apply(extract_product_code)

def categorize_price(price):
    if pd.isna(price):
        return "Unknown"
    price = float(price)
    if price < 10000:
        return "<10k"
    elif price < 15000:
        return "10k–15k"
    elif price < 25000:
        return "15k–25k"
    elif price < 40000:
        return "25k–40k"
    else:
        return "40k+"

df_men["price_range"] = df_men["price"].apply(categorize_price)

def categorize_price(price):
    if pd.isna(price):
        return "Unknown"
    price = float(price)
    if price < 10000:
        return "<10k"
    elif price < 15000:
        return "10k–15k"
    elif price < 25000:
        return "15k–25k"
    elif price < 40000:
        return "25k–40k"
    else:
        return "40k+"

df_women["price_range"] = df_women["price"].apply(categorize_price)

# Pivot table for product count per brand per price range
brand_price_matrix_men = df_men.pivot_table(
    index="brand",
    columns="price_range",
    values="product_name",
    aggfunc="count",
    fill_value=0
).reset_index()

# Add Total column
brand_price_matrix_men["total"] = brand_price_matrix_men.drop(columns=["brand"]).sum(axis=1)

# Optional: Reorder columns
ordered_cols = ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "<10k", "total"]
brand_price_matrix_men = brand_price_matrix_men.reindex(columns=[col for col in ordered_cols if col in brand_price_matrix_men.columns])
brand_price_matrix_men = brand_price_matrix_men.sort_values(by="Total", ascending=False).reset_index(drop=True)

# View result
#print(brand_price_matrix_men.head())

# Pivot table for product count per brand per price range
brand_price_matrix_women = df_women.pivot_table(
    index="brand",
    columns="price range",
    values="product name",
    aggfunc="count",
    fill_value=0
).reset_index()

# Add Total column
brand_price_matrix_women["total"] = brand_price_matrix_women.drop(columns=["brand"]).sum(axis=1)

# Optional: Reorder columns
ordered_cols = ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "<10k", "total"]
brand_price_matrix_women = brand_price_matrix_women.reindex(columns=[col for col in ordered_cols if col in brand_price_matrix_women.columns])

brand_price_matrix_women = brand_price_matrix_women.sort_values(by="Total", ascending=False).reset_index(drop=True)

brand_price_matrix_men.to_sql("men_price_range_top100", con=engine, if_exists="replace", index=False)
brand_price_matrix_women.to_sql("women_price_range_top100", con=engine, if_exists="replace", index=False)

