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

df_cleaned = pd.read_sql_table("product_price_cleaned", con=engine)

brand_code_counts = df_cleaned.groupby("brand")["product_code"].nunique()

# To see the result as a DataFrame:
brand_code_counts_df = brand_code_counts.reset_index(name="Unique Code Count")
#print(brand_code_counts_df)

summary = df_cleaned.groupby('brand').agg(
    Unique_Product_Codes=('product_code', 'nunique'),
    Total_Products=('brand', 'count')
).reset_index()

df_cleaned["product_name"] = df_cleaned["product_name"].astype(str).str.lower()

# Define unwanted keywords
unwanted_keywords = ["pocket watch", "repair tool", "watch bezel", "watch band", "tool","watch winder", "watch case"]

# Create a mask for rows that contain any of the unwanted terms
mask = df_cleaned["product_name"].apply(lambda x: any(keyword in x for keyword in unwanted_keywords))

# Drop those rows
df_cleaned = df_cleaned[~mask]

# Reset index (optional but clean)
df_cleaned.reset_index(drop=True, inplace=True)

print(f"Cleaned DataFrame. Remaining rows: {len(df_cleaned)}")

#Men and Women
def categorize_gender(product_name):
    if pd.isna(product_name):
        return "Unknown"

    name = str(product_name).lower().strip()

    men_keywords = ["boy", "boys", "man", "men", "male", "mens"]
    women_keywords = ["girl", "girls", "woman", "women", "female", "womens", "ladies","swarovski", "women_"]

    has_men = any(re.search(rf"\b{kw}\b", name) for kw in men_keywords)
    has_women = any(re.search(rf"\b{kw}\b", name) for kw in women_keywords)

    # Now, let’s make the logic smarter:
    if "couple" in name:
        return "Couple"
    elif "unisex" in name:
        return "Unisex"
    elif has_men and has_women:
        # Check whether both are part of **same segment** or just brand noise
        # Prefer classifying based on dominant terms
        if name.count("men") > name.count("women"):
            return "Men"
        elif name.count("women") > name.count("men"):
            return "Women"
        else:
            return "Unisex"
    elif has_women:
        return "Women"
    elif has_men:
        return "Men"
    else:
        return "Unknown"

df_cleaned["gender_category"] = df_cleaned["product_name"].apply(categorize_gender)
print(df_cleaned["gender_category"].value_counts())

df_cleaned["product_price"] = df_cleaned["product_price"].astype(str)
df_cleaned["product_price"] = df_cleaned["product_price"].str.replace("₹", "", regex=False)
df_cleaned["product_price"] = df_cleaned["product_price"].str.replace(",", "", regex=False).str.strip()

# Extract only the first valid numeric price (between 3 and 6 digits)
df_cleaned["product_price"] = df_cleaned["product_price"].str.extract(r'(\d{3,6})')

# Convert to numeric safely
df_cleaned["product_price"] = pd.to_numeric(df_cleaned["product_price"], errors="coerce")

##SKUs

# Step 1: Clean the 'product_price' column
df_cleaned["product_price"] = (
    df_cleaned["product_price"]
    .astype(str)
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.extract(r"(\d{4,6})")[0]
)
df_cleaned["product_price"] = pd.to_numeric(df_cleaned["product_price"], errors="coerce")

# Step 2: Define bins and labels
bins = [10000, 11000, 12000, 13000, 14000, 15000, 17500, 20000, 22500, 25000]
labels = [
    "10 - 11k", "11k-12k", "12k-13k", "13k-14k", "14k-15k",
    "15k-17.5k", "17.5-20k", "20k-22.5k", "22.5-25k"
]
df_cleaned["price_bin"] = pd.cut(df_cleaned["product_price"], bins=bins, labels=labels, right=False)

# Step 3: Filter brands
target_brands = ["Titan", "Titan Edge", "Fossil"]
df_filtered = df_cleaned[df_cleaned["brand"].isin(target_brands)]

# Step 4: Separate for Men and Women
df_men = df_filtered[df_filtered["gender_category"] == "Men"]
df_women = df_filtered[df_filtered["gender_category"] == "Women"]

# Step 5: Group and pivot
sku_table_men = df_men.groupby(["price_bin", "brand"]).size().unstack(fill_value=0).reindex(labels)
sku_table_women = df_women.groupby(["price_bin", "brand"]).size().unstack(fill_value=0).reindex(labels)


df_men.to_sql("sku_table_men", con=engine, if_exists="replace", index=False)
print("✅ Cleaned product_price saved as sku_table_men")

df_women.to_sql("sku_table_women", con=engine, if_exists="replace", index=False)
print("✅ Cleaned product_price saved as sku_table_women")


def categorize_price(price):
    if pd.isna(price):
        return "Unknown"
    try:
        price = float(price)
        if price < 10000:
            return "<10k"
        elif 10000 <= price < 15000:
            return "10k–15k"
        elif 15000 <= price < 25000:
            return "15k–25k"
        elif 25000 <= price < 40000:
            return "25k–40k"
        else:
            return "40k+"
    except:
        return "Unknown"

# Apply on your price column (replace 'Price' with actual column name if different)
df_cleaned["price_range"] = df_cleaned["product_price"].apply(categorize_price)

df_cleaned = df_cleaned[df_cleaned["price_range"] != "Unknown"].copy()

# Optional: Reset index
df_cleaned.reset_index(drop=True, inplace=True)

# Confirm it's dropped
print(df_cleaned["price_range"].value_counts())

brand_counts = df_cleaned["brand"].value_counts().reset_index()
brand_counts.columns = ["brand", "Product Count"]
print(brand_counts)

pivot_table = df_cleaned.pivot_table(
    index="brand",
    columns="price_range",
    values="product_code",
    aggfunc="nunique",
    fill_value=0
).reset_index()

# Reorder columns if needed
ordered_cols = ["brand", "<10k", "10k–15k", "15k–25k", "25k–40k", "40k+"]
pivot_table = pivot_table.reindex(columns=ordered_cols)

print(pivot_table)

df_cleaned["product_price"] = pd.to_numeric(df_cleaned["product_price"], errors='coerce')

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

df_cleaned["price_range"] = df_cleaned["product_price"].apply(categorize_price)

pivot_table = df_cleaned.pivot_table(
    index="brand",
    columns="price_range",
    values="product_code",
    aggfunc="nunique",
    fill_value=0
).reset_index()

# Reorder columns if needed
ordered_cols = ["brand", "<10k", "10k–15k", "15k–25k", "25k–40k", "40k+"]
pivot_table = pivot_table.reindex(columns=ordered_cols)

print(pivot_table)

df_cleaned.rename(columns={"product_code": "SKUs"}, inplace=True)

# 1. Products listed by brand, price_range, gender_category
product_count = df_cleaned.groupby(["brand", "price_range", "gender_category"])["product_name"].count().reset_index()
product_count.columns = ["brand", "price_range", "gender_category", "Product Count"]

# 2. Unique product_codes listed by brand, price_range, gender_category
unique_code_count = df_cleaned.groupby(["brand", "price_range", "gender_category"])["SKUs"].nunique().reset_index()
unique_code_count.columns = ["brand", "price_range", "gender_category", "SKUs"]

# Pivot Men tables
men_product_table = product_count[product_count["gender_category"] == "Men"].pivot_table(
    index="brand", columns="price_range", values="Product Count", fill_value=0).reset_index()
men_product_table = men_product_table.astype({col: 'int' for col in men_product_table.columns if col != "brand"})

men_code_table = unique_code_count[unique_code_count["gender_category"] == "Men"].pivot_table(
    index="brand", columns="price_range", values="SKUs", fill_value=0).reset_index()
men_code_table = men_code_table.astype({col: 'int' for col in men_code_table.columns if col != "brand"})

# Pivot Women tables
women_product_table = product_count[product_count["gender_category"] == "Women"].pivot_table(
    index="brand", columns="price_range", values="Product Count", fill_value=0).reset_index()
women_product_table = women_product_table.astype({col: 'int' for col in women_product_table.columns if col != "brand"})

women_code_table = unique_code_count[unique_code_count["gender_category"] == "Women"].pivot_table(
    index="brand", columns="price_range", values="SKUs", fill_value=0).reset_index()
women_code_table = women_code_table.astype({col: 'int' for col in women_code_table.columns if col != "brand"})

#Pivot All tables
all_product_table = df_cleaned.pivot_table(
    index="brand",
    columns="price_range",
    values="product_name",
    aggfunc="count",
    fill_value=0
).reset_index()
all_product_table = all_product_table.astype({col: 'int' for col in all_product_table.columns if col != "brand"})

all_sku_table = df_cleaned.pivot_table(
    index="brand",
    columns="price_range",
    values="SKUs",
    aggfunc="nunique",
    fill_value=0
).reset_index()

all_sku_table = all_sku_table.astype({col: 'int' for col in all_sku_table.columns if col != "brand"})


with pd.ExcelWriter(save_path, engine="xlsxwriter") as writer:
    men_product_table.to_excel(writer, sheet_name="Men - Product Count", index=False)
    women_product_table.to_excel(writer, sheet_name="Women - Product Count", index=False)
    men_code_table.to_excel(writer, sheet_name="Men - SKU Count", index=False)
    women_code_table.to_excel(writer, sheet_name="Women - SKU Count", index=False)
    all_product_table.to_excel(writer, sheet_name="All - Product Count", index=False)
    all_sku_table.to_excel(writer, sheet_name="All - SKU Count", index=False)


men_product_table.to_sql("Men - Product Count", con=engine, if_exists="replace", index=False)
women_product_table.to_sql("Women - Product Count",con=engine, if_exists="replace", index=False)
men_code_table.to_sql("Men - SKU Count",con=engine, if_exists="replace", index=False)
women_code_table.to_sql("Women - SKU Count",con=engine, if_exists="replace", index=False)
all_product_table.to_sql("All - Product Count", con=engine, if_exists="replace", index=False)
all_sku_table.to_sql("All - SKU Count", con=engine, if_exists="replace", index=False)


# Total product count per brand
brand_product_total = df_cleaned.groupby("brand")["product_name"].count().reset_index()
brand_product_total.columns = ["brand", "Total Product Count"]

# Total unique SKU count per brand
brand_sku_total = df_cleaned.groupby("brand")["SKUs"].nunique().reset_index()
brand_sku_total.columns = ["brand", "Total SKU Count"]

# Merge into one summary table
brand_totals = pd.merge(brand_product_total, brand_sku_total, on="brand")

top_1000 = df_cleaned.head(1000)

# Step 2: Total products per brand
top_1000_product_count = top_1000.groupby("brand")["product_name"].count().reset_index()
top_1000_product_count.columns = ["brand", "Top 1000 Product Count"]

# Step 3: Unique SKUs per brand
top_1000_sku_count = top_1000.groupby("brand")["SKUs"].nunique().reset_index()
top_1000_sku_count.columns = ["brand", "Top 1000 SKU Count"]

# Step 4: Merge both into one table
top_1000_summary = pd.merge(top_1000_product_count, top_1000_sku_count, on="brand")

# Step 2: Filter for Men and Women
top_men = top_1000[top_1000["gender_category"] == "Men"]
top_women = top_1000[top_1000["gender_category"] == "Women"]

# Step 3: Group and count for Men
men_product_count = top_men.groupby("brand")["product_name"].count().reset_index()
men_product_count.columns = ["brand", "Men - Product Count (Top 1000)"]

men_sku_count = top_men.groupby("brand")["SKUs"].nunique().reset_index()
men_sku_count.columns = ["brand", "Men - SKU Count (Top 1000)"]

# Step 4: Group and count for Women
women_product_count = top_women.groupby("brand")["product_name"].count().reset_index()
women_product_count.columns = ["brand", "Women - Product Count (Top 1000)"]

women_sku_count = top_women.groupby("brand")["SKUs"].nunique().reset_index()
women_sku_count.columns = ["brand", "Women - SKU Count (Top 1000)"]

# Add a rank column if not already present (based on position)
df_cleaned = df_cleaned.reset_index(drop=True)
df_cleaned["Position"] = df_cleaned.index + 1  # Rank starts from 1

# Get the first (best) appearance of each brand
best_rank_by_brand = df_cleaned.groupby("brand")["Position"].min().reset_index()
best_rank_by_brand.columns = ["brand", "Best Rank (First Appearance)"]

#all_sku_table.to_sql"All - SKU Count", con=engine, if_exists="replace", index=False)

top_1000_product_count.to_sqll("Top 1000 - Product Count", con=engine, if_exists="replace", index=False)
top_1000_sku_count.to_sql("Top 1000 - SKU Count", con=engine, if_exists="replace", index=False)
men_product_count.to_sql("Men - Product Count", con=engine, if_exists="replace", index=False)
men_sku_count.to_sql("Men - SKU Count", con=engine, if_exists="replace", index=False)
women_product_count.to_sql("Women - Product Count", con=engine, if_exists="replace", index=False)
women_sku_count.to_sql("Women - SKU Count", con=engine, if_exists="replace", index=False)
best_rank_by_brand.to_sql("Best Rank_All", con=engine, if_exists="replace", index=False)



