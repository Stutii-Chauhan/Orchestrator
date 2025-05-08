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

    st.markdown(f"### 🔥 Best Sellers for {gender}")

    # Sidebar Filters
    st.sidebar.markdown("### Select Gender")
    st.sidebar.radio("Choose Best Seller Category", ["Men", "Women"], index=0 if gender == "Men" else 1, key="selected_gender_radio")

    st.sidebar.markdown("### Filter Products")

    selected_brands = st.sidebar.multiselect("Brand", options=sorted(df["Brand"].dropna().unique()))
    selected_materials = st.sidebar.multiselect("Band Material", options=sorted(df["Band Material"].dropna().unique()))
    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    # Filtering
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
        with st.container():
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if pd.notna(row.get("ImageURL")):
                        st.image(row["ImageURL"], width=140)
                    else:
                        st.write("🖼️ Image not available")

                with col2:
                    st.markdown(
                        f"""<h4 style='margin-bottom:0; text-align: left;'>
                                <a href="{row['URL']}" style='text-decoration: none; color: black;' target="_blank">
                                    {row['Product Name']}
                                </a>
                            </h4>""",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Brand:** {row['Brand']}", unsafe_allow_html=True)
                    st.markdown(f"**Model Number:** {row['Model Number']}", unsafe_allow_html=True)
                    st.markdown(f"**Price:** ₹{int(row['Price'])}", unsafe_allow_html=True)
                    st.markdown(f"**Rating:** {row['Ratings'] if pd.notna(row['Ratings']) else 'N/A'}/5", unsafe_allow_html=True)

                    discount = row["Discount"]
                    if pd.notna(discount) and str(discount).strip().upper() != "N/A" and "%" not in str(discount):
                        st.markdown(f"**Discount:** {discount}%", unsafe_allow_html=True)
                    elif pd.notna(discount) and "%" in str(discount):
                        st.markdown(f"**Discount:** {discount}", unsafe_allow_html=True)
                    else:
                        st.markdown("**Discount:** N/A", unsafe_allow_html=True)

                # Divider between products
                if i < len(filtered_df) - 1:
                    st.markdown("<hr style='margin-top: 1rem; margin-bottom: 1rem;'>", unsafe_allow_html=True)

# ---- Page Setup ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.markdown("## 📦 Explore Best Sellers")

# Gender selector in sidebar
if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "Men"

# Update gender from sidebar radio
st.session_state.selected_gender = st.sidebar.radio(
    "Choose Best Seller Category",
    ["Men", "Women"],
    index=0 if st.session_state.selected_gender == "Men" else 1,
    key="selected_gender"
)

# Render section
render_best_sellers(st.session_state.selected_gender)
