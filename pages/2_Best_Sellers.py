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
    
    # Clean price column: remove commas, convert to int, drop NAs
    df["Price"] = (
        df["Price"]
        .astype(str)
        .str.replace(",", "")
        .str.extract("(\d+)")
        .astype(float)
        .dropna()
    )

    return df

# ---- Display Best Sellers ----
def render_best_sellers(gender):
    table = "Final_Watch_Dataset_Men_output" if gender == "Men" else "Final_Watch_Dataset_Women_output"
    df = load_data(table)

    st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect(
        "Brand", options=sorted(df["Brand"].dropna().unique())
    )

    selected_materials = st.sidebar.multiselect(
        "Band Material", options=sorted(df["Band Material"].dropna().unique())
    )

    if df["Price"].isnull().all():
        st.warning("Price data not found or malformed.")
        return

    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    # Filtering
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["Band Material"].isin(selected_materials)]
    filtered_df = filtered_df[(filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])]

    if filtered_df.empty:
        st.warning("No products found with selected filters.")
    else:
        for _, row in filtered_df.iterrows():
            col1, col2 = st.columns([1, 2])
            with col1:
                if pd.notna(row.get("ImageURL")):
                    st.image(row["ImageURL"], width=200)
                else:
                    st.write("🖼️ Image not available")
            with col2:
                # Make product name clickable
                if pd.notna(row.get("URL")):
                    product_link = f"[{row['Product Name']}]({row['URL']})"
                else:
                    product_link = row['Product Name']

                st.subheader(product_link)

                st.write(f"**Brand:** {row['Brand']}")
                st.write(f"**Model Number:** {row['Model Number']}")
                st.write(f"**Price:** ₹{int(row['Price'])}")

                # Ratings
                rating = row.get("Ratings")
                st.write(f"**Rating:** {rating}/5" if pd.notna(rating) else "**Rating:** N/A")

                # Discount
                discount = row.get("Discount")
                if pd.notna(discount):
                    discount_clean = str(discount).strip().rstrip('%')
                    st.write(f"**Discount:** {discount_clean}%")
                else:
                    st.write("**Discount:** N/A")

            st.markdown("---")

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.title("📦 Explore Best Sellers")

col1, col2 = st.columns(2)
if col1.button("🕺 Best Sellers for Men"):
    render_best_sellers("Men")
if col2.button("💃 Best Sellers for Women"):
    render_best_sellers("Women")
