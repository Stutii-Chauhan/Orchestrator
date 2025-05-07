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

    # st.subheader(f"🔥 Best Sellers for {gender}")
    st.sidebar.header("Filter Products")

    selected_brands = st.sidebar.multiselect(
        "Brand", options=sorted(df["Brand"].dropna().unique())
    )

    selected_materials = st.sidebar.multiselect(
        "Band Material", options=sorted(df["Band Material"].dropna().unique())
    )

    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    # Filtering
    filtered_df = df.copy()
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["Band Material"].isin(selected_materials)]
    filtered_df = filtered_df[
        (filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])
    ]

    # Display
    if filtered_df.empty:
        st.warning("No products found with selected filters.")
    else:
        for _, row in filtered_df.iterrows():
            col1, col2 = st.columns([1, 2])
            with col1:
                if pd.notna(row.get("ImageURL")):
                    st.image(row["ImageURL"], width=180)
                else:
                    st.write("🖼️ Image not available")
            with col2:
                # st.markdown(f"### [{row['Product Name']}]({row['URL']})")
                st.markdown(
                    f"""<h4 style='margin-bottom:0'>
                            <a href="{row['URL']}" style='text-decoration: none; color: black;' target="_blank">
                                {row['Product Name']}
                            </a>
                        </h4>""",
                    unsafe_allow_html=True,
                )
                st.write(f"**Brand:** {row['Brand']}")
                st.write(f"**Model Number:** {row['Model Number']}")
                st.write(f"**Price:** ₹{int(row['Price'])}")
                st.write(f"**Rating:** {row['Ratings'] if pd.notna(row['Ratings']) else 'N/A'}/5")
                discount = row["Discount"]
                if pd.notna(discount) and str(discount).strip().upper() != "N/A" and "%" not in str(discount):
                    st.write(f"**Discount:** {discount}%")
                elif pd.notna(discount) and "%" in str(discount):
                    st.write(f"**Discount:** {discount}")
                else:
                    st.write("**Discount:** N/A")

        st.markdown("---")

# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
st.title("📦 Explore Best Sellers")

# Session variable to store gender selection
if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = None

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🕺 Best Sellers for Men"):
        st.session_state.selected_gender = "Men"
with col2:
    if st.button("💃 Best Sellers for Women"):
        st.session_state.selected_gender = "Women"

# Render selected gender
if st.session_state.selected_gender:
    render_best_sellers(st.session_state.selected_gender)
