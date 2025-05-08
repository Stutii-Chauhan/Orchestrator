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
    df["Price"] = pd.to_numeric(df["Price"].str.replace(",", "").fillna("0"), errors="coerce").astype(int)
    return df

# ---- Display Best Sellers ----
def render_best_sellers(gender):
    table = "Final_Watch_Dataset_Men_output" if gender == "Men" else "Final_Watch_Dataset_Women_output"
    df = load_data(table)

    st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect("Brand", options=sorted(df["Brand"].dropna().unique()))
    selected_materials = st.sidebar.multiselect("Price Band", options=sorted(df["price_band"].dropna().unique()))

    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    # Filtering
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["price_band"].isin(selected_materials)]
    filtered_df = filtered_df[(filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])]

    # Display
    if filtered_df.empty:
        st.warning("No products found with selected filters.")
    else:
        rows = list(filtered_df.iterrows())
        for i in range(0, len(rows), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(rows):
                    _, row = rows[i + j]
                    with cols[j]:
                        if pd.notna(row.get("ImageURL")):
                            st.image(row["ImageURL"], width=160)
                        else:
                            st.write("🖼️ Image not available")

                        product_name = row['Product Name']
                        display_name = product_name[:60] + "..." if len(product_name) > 60 else product_name

                        st.markdown(
                            f"""
                            <div style='line-height: 1.4; min-height: 60px; font-size: 1.1rem; font-weight: bold'>
                                {display_name}
                            </div>
                            <div style='line-height: 1.6; font-size: 0.95rem'>
                                <b>Brand:</b> {row['Brand']}<br>
                                <b>Model Number:</b> {row['Model Number']}<br>
                                <b>Price:</b> ₹{int(row['Price'])}<br>
                                <b>Rating:</b> {row['Ratings'] if pd.notna(row['Ratings']) else 'N/A'}/5<br>
                                <b>Discount:</b> {str(row['Discount']) if pd.notna(row['Discount']) else 'N/A'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.title("📦 Explore Best Sellers")

# Session default initialization
if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "Men"

# Sidebar gender selector
st.sidebar.markdown("### Select Gender")
st.sidebar.radio("Choose Best Seller Category", ["Men", "Women"], key="selected_gender")

# Render based on gender selection
render_best_sellers(st.session_state.selected_gender)
