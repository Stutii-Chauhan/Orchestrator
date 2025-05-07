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
    return pd.read_sql_table(table_name, con=engine)

# ---- Display Best Sellers ----
def render_best_sellers(gender):
    table = "top100_men_filled" if gender == "Men" else "top100_women_filled"
    df = load_data(table)

    # st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect(
        "Brand", options=sorted(df["brand"].dropna().unique())
    )

    price_min, price_max = int(df["price"].min()), int(df["price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    selected_materials = st.sidebar.multiselect(
        "Band Material", options=sorted(df["band_material"].dropna().unique())
    )

    # Filtering
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["band_material"].isin(selected_materials)]
    filtered_df = filtered_df[(filtered_df["price"] >= selected_price[0]) & (filtered_df["price"] <= selected_price[1])]

    # Display
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
                st.subheader(f"{row['product_name']} - ₹{int(row['price'])}")
                st.write(f"**Brand:** {row['brand']}")
                st.write(f"**Model Number:** {row['model_number']}")
                rating = row.get('rating(out_of_5)')
                discount = row.get('discount_(%)')
                
                st.write(f"**Rating:** {str(rating) + '/5' if pd.notna(rating) else 'N/A'}")
                st.write(f"**Discount:** {str(discount) + '%' if pd.notna(discount) else 'N/A'}")

        st.markdown("---")

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="🔥")
st.title("🛍️ Explore Best Sellers")

col1, col2 = st.columns(2)
if col1.button("🕺 Best Sellers for Men"):
    render_best_sellers("Men")
elif col2.button("💃 Best Sellers for Women"):
    render_best_sellers("Women")
