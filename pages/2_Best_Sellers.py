import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ------------------------
# Supabase DB Connection
# ------------------------
DB = st.secrets["SUPABASE_DB"]
USER = st.secrets["SUPABASE_USER"]
PASSWORD = quote_plus(st.secrets["SUPABASE_PASSWORD"])
HOST = st.secrets["SUPABASE_HOST"]
PORT = st.secrets["SUPABASE_PORT"]
engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")

# ------------------------
# Load Data (Case-Sensitive)
# ------------------------
@st.cache_data(ttl=600)
def load_data(table_name):
    return pd.read_sql(f'SELECT * FROM "{table_name}"', con=engine)

# ------------------------
# Best Sellers Renderer
# ------------------------
def render_best_sellers(gender):
    table = "Final_Watch_Dataset_Men_output" if gender == "Men" else "Final_Watch_Dataset_Women_output"
    df = load_data(table)

    st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect("Brand", options=sorted(df["Brand"].dropna().unique()))
    selected_materials = st.sidebar.multiselect("Band Material", options=sorted(df["Band Material"].dropna().unique()))

    # Price Range
    try:
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
        selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))
    except:
        st.warning("Price data not found or malformed.")
        selected_price = (0, 999999)

    # Filter Data
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["Band Material"].isin(selected_materials)]
    filtered_df = filtered_df[(filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])]

    # Display
    if filtered_df.empty:
        st.warning("No products found with selected filters.")
    else:
        for _, row in filtered_df.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                image_url = row.get("ImageURL")
                if pd.notna(image_url) and isinstance(image_url, str):
                    st.image(image_url, width=200)
                else:
                    st.write("🖼️ Image not available")

            with col2:
                st.subheader(f"{row['Product Name']} - ₹{int(float(row['Price'])) if pd.notna(row['Price']) else 'N/A'}")
                st.write(f"**Brand:** {row.get('Brand', 'N/A')}")
                st.write(f"**Model Number:** {row.get('Model Number', 'N/A')}")
                
                rating = row.get("Ratings", "N/A")
                rating_str = f"{rating}/5" if pd.notna(rating) and rating != "N/A" else "N/A"
                st.write(f"**Rating:** {rating_str}")

                discount = row.get("Discount", "N/A")
                discount_str = f"{discount}%" if pd.notna(discount) and discount != "N/A" else "N/A"
                st.write(f"**Discount:** {discount_str}")

        st.markdown("---")

# ------------------------
# Main App Layout
# ------------------------
st.set_page_config(page_title="Best Sellers", page_icon="📦", layout="centered")
st.title("📦 Explore Best Sellers")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🕺 Best Sellers for Men"):
        render_best_sellers("Men")
with col2:
    if st.button("💃 Best Sellers for Women"):
        render_best_sellers("Women")
