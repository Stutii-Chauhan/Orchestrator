import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ---- Supabase DB Connection ----
DB = st.secrets["SUPABASE_DB"]
USER = st.secrets["SUPABASE_USER"]
PASSWORD = quote_plus(st.secrets["SUPABASE_PASSWORD"])
HOST = st.secrets["SUPABASE_HOST"]
PORT = st.secrets["SUPABASE_PORT"]
engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")

# ---- Load Data ----
@st.cache_data(ttl=600)
def load_data(table_name):
    df = pd.read_sql_table(table_name, con=engine)
    df.columns = df.columns.str.lower()  # normalize column names to lowercase
    return df

# ---- Display Best Sellers ----
def render_best_sellers(gender):
    table = "final_watch_dataset_men_output" if gender == "Men" else "final_watch_dataset_women_output"
    df = load_data(table)

    st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    # Convert numeric columns and drop NaN prices
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["ratings"] = pd.to_numeric(df["ratings"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce")
    df.dropna(subset=["price"], inplace=True)

    # Filters
    selected_brands = st.sidebar.multiselect(
        "Brand", options=sorted(df["brand"].dropna().unique())
    )
    price_min, price_max = int(df["price"].min()), int(df["price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))
    selected_materials = st.sidebar.multiselect(
        "Band Material", options=sorted(df["band material"].dropna().unique())
    )

    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["band material"].isin(selected_materials)]
    filtered_df = filtered_df[
        (filtered_df["price"] >= selected_price[0]) & (filtered_df["price"] <= selected_price[1])
    ]

    # Display products
    if filtered_df.empty:
        st.warning("No products found with selected filters.")
    else:
        for _, row in filtered_df.iterrows():
            col1, col2 = st.columns([1, 2])
            with col1:
                if pd.notna(row.get("imageurl")):
                    st.image(row["imageurl"], width=200)
                else:
                    st.write("🖼️ Image not available")
            with col2:
                st.subheader(f"{row['product name']} - ₹{int(row['price'])}")
                st.write(f"**Brand:** {row['brand']}")
                st.write(f"**Model Number:** {row['model number']}")
                rating = f"{row['ratings']}/5" if pd.notna(row['ratings']) else "N/A"
                discount = f"{row['discount']}%" if pd.notna(row['discount']) else "N/A"
                st.write(f"**Rating:** {rating}")
                st.write(f"**Discount:** {discount}")
        st.markdown("---")

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.title("📦 Explore Best Sellers")

col1, col2 = st.columns(2)
if col1.button("🕺 Best Sellers for Men"):
    render_best_sellers("Men")
elif col2.button("💃 Best Sellers for Women"):
    render_best_sellers("Women")
