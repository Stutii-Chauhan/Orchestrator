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

    selected_brands = st.sidebar.multiselect("Brand", sorted(df["Brand"].dropna().unique()))
    selected_materials = st.sidebar.multiselect("Price Band", sorted(df["price_band"].dropna().unique()))
    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["price_band"].isin(selected_materials)]
    filtered_df = filtered_df[
        (filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])
    ]

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
                        st.markdown(
                            f"""
                            <div style="border:1px solid #ddd; padding:15px; border-radius:8px; 
                                        box-shadow:2px 2px 10px #eee; min-height:480px">
                                <div style='text-align:center'>
                                    <img src="{row['ImageURL']}" width="140"/>
                                </div>
                                <div style="font-weight:bold; font-size:1.05rem; margin-top:10px; 
                                            min-height:60px; overflow:hidden; text-overflow:ellipsis">
                                    {row['Product Name'][:70] + ('...' if len(row['Product Name']) > 70 else '')}
                                </div>
                                <div style="font-size:0.95rem; line-height:1.6">
                                    <b>Brand:</b> {row['Brand']}<br>
                                    <b>Model Number:</b> {row['Model Number']}<br>
                                    <b>Price:</b> ₹{int(row['Price'])}<br>
                                    <b>Rating:</b> {row['Ratings'] if pd.notna(row['Ratings']) else 'N/A'}/5<br>
                                    <b>Discount:</b> {str(row['Discount']) if pd.notna(row['Discount']) else 'N/A'}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            # Spacing between rows
            st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.title("📦 Explore Best Sellers")

if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "Men"

st.sidebar.markdown("### Select Gender")
st.sidebar.radio("Choose Best Seller Category", ["Men", "Women"], key="selected_gender")

render_best_sellers(st.session_state.selected_gender)
