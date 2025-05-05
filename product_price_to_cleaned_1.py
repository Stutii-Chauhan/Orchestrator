import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus


# ------------------------------------
# DB Setup
# ------------------------------------
db = os.environ["SUPABASE_DB"]
user = os.environ["SUPABASE_USER"]
raw_password = os.environ["SUPABASE_PASSWORD"]
host = os.environ["SUPABASE_HOST"]
port = os.environ["SUPABASE_PORT"]
password = quote_plus(raw_password)

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

import pandas as pd
import re
# ------
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
    Extracts a product code from the product name.
    Steps:
      1. Tokenize the product name with a regex that captures letters, digits, underscores, dashes, slashes, and periods.
      2. Keep tokens that either (a) contain both letters and digits, or (b) are all digits and at least 4 characters long.
      3. For tokens containing underscores or slashes, split them further.
      4. Choose the candidate token that appears nearest to the end of the product name.
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

    # Choose the candidate that appears nearest to the end of the product name.
    last_candidate_uncleaned = None
    last_index = -1
    for token in final_candidates:
        index = product_name.rfind(token)
        if index > last_index:
            last_index = index
            last_candidate_uncleaned = token

    final_token = clean_token(last_candidate_uncleaned)

    return final_token.upper() if final_token else None

import pandas as pd

def extract_brand(product_name):
    if pd.isna(product_name):
        return None

    product_name_lower = product_name.lower()

    if "xylys" in product_name_lower:
        return "Titan XYLYS"

    brand_mapping = {
        "tommy hilfiger": "Tommy Hilfiger",
        "tommy": "Tommy Hilfiger",
        "armani exchange": "Armani Exchange",
        "diesel": "Diesel",
        "fossil": "Fossil",
        "titan edge": "Titan Edge",
        "titan": "Titan",
        "casio": "Casio",
        "michael kors": "Michael Kors",
        "maserati": "Maserati",
        "luminox": "Luminox",
        "zeppelin": "Zeppelin",
        "seiko": "Seiko",
        "ted baker": "Ted Baker",
        "invicta": "Invicta",
        "citizen": "Citizen",
        "emporio armani": "Emporio Armani",
        "guess": "Guess",
        "fiece": "Fiece",
        "just cavalli": "Just Cavalli",
        "earnshaw": "Earnshaw",
        "alba": "Alba",
        "daniel wellington": "Daniel Wellington",
        "police": "Police",
        "olevs": "Olevs",
        "ducati": "Ducati",
        "mathey-tissot": "Mathey-Tissot",
        "timex": "Timex",
        "swarovski": "Swarovski",
        "nautica": "Nautica",
        "swiss military hanowa": "Swiss Military Hanowa",
        "lacoste": "Lacoste",
        "boss": "Boss",
        "anne klein": "Anne Klein",
        "calvin klein": "Calvin Klein",
        "pierre cardin": "Pierre Cardin",
        "coach": "Coach",
        "p philip": "P Philip",
        "tag heuer": "Tag Heuer",
        "kenneth cole": "Kenneth Cole",
        "philipp plein": "Philipp Plein",
        "guy laroche": "Guy Laroche",
        "carlos philip": "Carlos Philip",
        "adidas": "Adidas",
        "movado": "Movado",
        "daniel klein": "Daniel Klein",
        "sonata": "Sonata",
        "d1 milano": "D1 Milano",
        "alexandre christie": "Alexandre Christie",
        "santa barbara": "Santa Barbara Polo & Racquet Club",
        "mini cooper": "MINI Cooper",
        "hanowa": "Hanowa",
        "charles-hubert": "Charles-Hubert",
        "gc": "GC"
    }

    sorted_keys = sorted(brand_mapping.keys(), key=lambda x: len(x), reverse=True)
    for key in sorted_keys:
        if key in product_name_lower:
            return brand_mapping[key]
    return "Others"

try:
    df = pd.read_sql_table("product_price", con=engine)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Ensure required columns exist
    if "product_name" not in df.columns or "product_price" not in df.columns:
        raise KeyError("Required columns 'Product Name' and/or 'Product Price' not found.")

    df = df.dropna(subset=["product_name", "product_price"])
    df["product_code"] = df["product_name"].apply(extract_product_code)
    df["brand"] = df["product_name"].apply(extract_brand)

    # Save if needed
    # df.to_sql("product_price_output", con=engine, if_exists="replace", index=False)
    # print("✅ Cleaned product_price saved as product_price_output")

except Exception as e:
    print(f"❌ Failed cleaning product_price: {e}")

# print("🧾 Columns in DataFrame:", df.columns.tolist())

['product_url', 'product_name', 'product_price', 'model_number', 'asin', 'brand_name', 'product_code', 'brand']

# # # df.head(25)
brand_code_counts = df.groupby("brand")["product_code"].nunique()

# To see the result as a DataFrame:
brand_code_counts_df = brand_code_counts.reset_index(name="Unique Code Count")

#print(brand_code_counts_df)

titan_edge_df = df[df["brand"].str.upper() == "TITAN EDGE"]

# Get the unique product codes for Titan Edge
titan_edge_codes = titan_edge_df["product_code"].unique()

print(titan_edge_codes)

grouped = df.groupby(["product_name", "product_code"]).size().reset_index(name="Count")

# Filter groups where count > 1 (i.e. duplicate rows)
duplicates = grouped[grouped["Count"] > 1]

print(duplicates)

df = df.drop_duplicates(subset=["product_name", "product_code"], keep="first")

df.loc[
    (df["product_name"] == "Titan Edge Men’s Designer Watch – Slim, Quartz, Water Resistant") &
    (df["product_code"].isnull()),
    "product_code"
] = "1683NL01"

df = df.drop(columns=["model_number", "asin","brand_name"])

df.to_sql("product_price_cleaned", con=engine, if_exists="replace", index=False)
print("✅ Cleaned product_price saved as product_price_cleaned")
