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

    st.sidebar.header("Filter Products")

    # 1. Price Band (Checkboxes)
    st.sidebar.markdown("**Price Band**")
    df["price_band"] = df["price_band"].str.strip().str.upper()
    price_band_options = sorted(df["price_band"].dropna().unique())
    selected_priceband = []
    for band in price_band_options:
        if st.sidebar.checkbox(band, key=f"price_band_{band}"):
            selected_priceband.append(band)

    # 2. Price Range Slider
    price_min, price_max = int(df["Price"].min()), int(df["Price"].max())
    selected_price = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

    # 3. Brand
    df["Brand"] = df["Brand"].str.strip().str.lower().str.title()
    selected_brands = st.sidebar.multiselect("Brand", sorted(df["Brand"].dropna().unique()))

    # 4. Dial Colour
    df["Dial Colour"] = df["Dial Colour"].str.strip().str.lower().str.title()
    selected_dialcol = st.sidebar.multiselect("Dial Colour", sorted(df["Dial Colour"].dropna().unique()))

    # 5. Dial Shape
    df["Case Shape"] = df["Case Shape"].str.strip().str.lower().str.title()
    selected_dialshape = st.sidebar.multiselect("Dial Shape", sorted(df["Case Shape"].dropna().unique()))
    
    # 6. Band Colour
    df["Band Colour"] = df["Band Colour"].str.strip().str.lower().str.title()
    selected_bandcol = st.sidebar.multiselect("Band Colour", sorted(df["Band Colour"].dropna().unique()))

    # 7. Band Material
    df["Band Material"] = df["Band Material"].str.strip().str.lower().str.title()
    selected_bandmaterial = st.sidebar.multiselect("Band Material", sorted(df["Band Material"].dropna().unique()))



    # Apply filters
    filtered_df = df.copy()
    if selected_priceband:
        filtered_df = filtered_df[filtered_df["price_band"].isin(selected_priceband)]
    filtered_df = filtered_df[
        (filtered_df["Price"] >= selected_price[0]) & (filtered_df["Price"] <= selected_price[1])
    ]
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Brand"].isin(selected_brands)]
    if selected_dialcol:
        filtered_df = filtered_df[filtered_df["Dial Colour"].isin(selected_dialcol)]
    if selected_bandcol:
        filtered_df = filtered_df[filtered_df["Band Colour"].isin(selected_bandcol)]
    if selected_dialshape:
        filtered_df = filtered_df[filtered_df["Case Shape"].isin(selected_dialshape)]
    if selected_bandmaterial:
        filtered_df = filtered_df[filtered_df["Band Material"].isin(selected_bandmaterial)]

    # Pagination
    items_per_page = 6
    total_items = len(filtered_df)
    total_pages = (total_items - 1) // items_per_page + 1
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
                                    <b>Rating:</b> {
                                        f"{int(row['Ratings'])}/5" if pd.notna(row['Ratings']) and row['Ratings'].is_integer()
                                        else f"{round(row['Ratings'], 1)}/5" if pd.notna(row['Ratings'])
                                        else "N/A"
                                    }<br>
                                    <b>Discount:</b> {
                                        "No" if pd.notna(row["Discount"]) and row["Discount"] in ["0", "0.0"]
                                        else row["Discount"] if pd.notna(row["Discount"])
                                        else "N/A"
                                    }
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Pagination Controls
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 6, 1])

        with col1:
            if st.session_state.page_number > 1:
                if st.button("⬅️ Prev"):
                    st.session_state.page_number -= 1

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

        with col3:
            if st.session_state.page_number < total_pages:
                if st.button("Next ➡️"):
                    st.session_state.page_number += 1



# ---- Main UI ----
st.set_page_config(page_title="Best Sellers", page_icon="📦")
# st.title(f" Best Sellers for {gender}")

if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "Men"

st.sidebar.markdown("### Gender Category")
st.sidebar.radio("Select the Gender", ["Men", "Women"], key="selected_gender")

render_best_sellers(st.session_state.selected_gender)
