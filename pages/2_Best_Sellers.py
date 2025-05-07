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
    table = "Final_Watch_Dataset_Men_output" if gender == "Men" else "Final_Watch_Dataset_Women_output"
    df = load_data(table)

    # Clean numeric columns
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Ratings"] = pd.to_numeric(df["Ratings"], errors="coerce")
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")
    df.dropna(subset=["Price"], inplace=True)

    st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect(
        "Brand", options=sorted(df["Brand"].dropna().unique())
    )

    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    selected_materials = st.sidebar.multiselect(
        "Band Material", options=sorted(df["Band Material"].dropna().unique())
    )

    # Apply filters
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["Band Material"].isin(selected_materials)]
    filtered_df = filtered_df[(filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])]

    # Display products
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
                st.subheader(f"{row['Product Name']} - ₹{int(row['Price'])}")
                st.write(f"**Brand:** {row['Brand']}")
                st.write(f"**Model Number:** {row['Model Number']}")
                rating = f"{row['Ratings']}/5" if pd.notna(row['Ratings']) else "N/A"
                discount = f"{row['Discount']}%" if pd.notna(row['Discount']) else "N/A"
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
