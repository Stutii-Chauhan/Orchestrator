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

        # --- Pagination Controls ---
        # --- Pagination Controls ---
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 4, 1])
        
        # Previous
        with col1:
            if st.session_state.page_number > 1:
                if st.button("⬅️ Prev"):
                    st.session_state.page_number -= 1
        
        # Dynamic page numbers in the center
        with col2:
            current = st.session_state.page_number
            window = 2  # Show 2 pages before and after
            page_range = []
        
            if current > window + 1:
                page_range.append("1")
                if current > window + 2:
                    page_range.append("...")
        
            for i in range(max(1, current - window), min(total_pages + 1, current + window + 1)):
                page_range.append(str(i))
        
            if current + window < total_pages:
                if current + window + 1 < total_pages:
                    page_range.append("...")
                page_range.append(str(total_pages))
        
            page_links_html = []
            for p in page_range:
                if p == str(current):
                    page_links_html.append(f"<b>{p}</b>")
                elif p == "...":
                    page_links_html.append("...")
                else:
                    page_links_html.append(
                        f"<a href='#' onclick='window.parent.postMessage({{\"page\": {p}}}, \"*\")'>{p}</a>"
                    )
        
            st.markdown(
                f"""
                <div style='text-align:center; font-size: 16px;'>
                    {" | ".join(page_links_html)}
                </div>
                """,
                unsafe_allow_html=True
            )
        
            # Add a hidden form for Streamlit-safe input switching
            page_clicked = st.selectbox("Page Navigation", list(range(1, total_pages + 1)), index=current - 1, label_visibility="collapsed")
            if page_clicked != current:
                st.session_state.page_number = page_clicked
        
        # Next
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
