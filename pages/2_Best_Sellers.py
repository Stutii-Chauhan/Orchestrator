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

@st.cache_data(ttl=600)
def load_data(table_name):
    df = pd.read_sql_table(table_name, con=engine)
    df["Price"] = pd.to_numeric(df["Price"].str.replace(",", "").fillna("0"), errors="coerce").astype(int)
    return df

def render_best_sellers(gender):
    st.title(f" Best Sellers for {gender}")
    table = "Final_Watch_Dataset_Men_output" if gender == "Men" else "Final_Watch_Dataset_Women_output"
    df = load_data(table)

    # st.subheader(f"🔥 Best Sellers for {gender}")
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

    # Pagination settings
    items_per_page = 6
    total_items = len(filtered_df)
    total_pages = (total_items - 1) // items_per_page + 1

    # Session state for page
    if "page_number" not in st.session_state:
        st.session_state.page_number = 1

    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paged_df = filtered_df.iloc[start_idx:end_idx]

    if paged_df.empty:
        st.warning("No products found with selected filters.")
    else:
        st.markdown(f"**Showing {start_idx + 1}–{min(end_idx, total_items)} of {total_items} products**")

        rows = list(paged_df.iterrows())
        
        for i in range(0, len(rows), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(rows):
                    _, row = rows[i + j]
                    with cols[j]:
                        st.markdown(
                            f"""
                            <div style="border:1px solid #ddd; padding:15px; border-radius:8px; 
                                        box-shadow:2px 2px 10px #eee; height:540px; 
                                        display: flex; flex-direction: column; justify-content: space-between;">
                                <div style='text-align:center'>
                                    <a href="{row['URL']}" target="_blank">
                                        <img src="{row['ImageURL']}" style="height:240px; object-fit:contain; margin:auto; display:block; margin-bottom:15px;" />
                                    </a>
                                </div>
                                <div style="font-weight:bold; font-size:1.05rem; margin-top:7.5px;
                                            display: -webkit-box;
                                            -webkit-line-clamp: 2;
                                            -webkit-box-orient: vertical;
                                            overflow: hidden;
                                            height: 3em;
                                            line-height: 1.5em;"
                                     title="{row['Product Name']}">
                                    {row['Product Name']}
                                </div>
                                <div style="font-size:0.95rem; line-height:1.6">
                                    <b>Brand:</b> {row['Brand']}<br>
                                    <b>Model Number:</b> {row['Model Number']}<br>
                                    <b>Price:</b> ₹{int(row['Price'])}<br>
                                    <b>Rating:</b> {row['Ratings'] if pd.notna(row['Ratings']) else 'N/A'}/5<br>
                                    <b>Discount:</b> {
                                        "No" if pd.notna(row["Discount"]) and row["Discount"] in ["0", "0.0"]
                                        else row["Discount"] + "%" if pd.notna(row["Discount"])
                                        else "N/A"
                                    }
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            # Add vertical space between rows
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # --- Pagination Controls ---
        # --- Pagination Controls ---
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 6, 1])
        
        # Prev button
        with col1:
            if st.session_state.page_number > 1:
                if st.button("⬅️ Prev"):
                    st.session_state.page_number -= 1
        
        # Page number buttons
        with col2:
            current = st.session_state.page_number
            window = 2
            page_range = list(range(max(1, current - window), min(total_pages + 1, current + window + 1)))
        
            page_buttons = st.columns(len(page_range))
            for idx, page in enumerate(page_range):
                if page == current:
                    page_buttons[idx].button(f"• {page} •", disabled=True)
                else:
                    if page_buttons[idx].button(str(page)):
                        st.session_state.page_number = page
        
        # Next button
        with col3:
            if st.session_state.page_number < total_pages:
                if st.button("Next ➡️"):
                    st.session_state.page_number += 1



# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
# st.title(f" Best Sellers for {gender}")

if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "Men"

st.sidebar.markdown("### Select Gender")
st.sidebar.radio("Choose Best Seller Category", ["Men", "Women"], key="selected_gender")

render_best_sellers(st.session_state.selected_gender)
