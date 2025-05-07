import streamlit as st
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Waqt Home", page_icon="⌚", layout="centered")

st.title("Welcome to Waqt ⌚")
st.markdown("#### What would you like to explore today?")

# Styling
card_style = """
<style>
    .card {
        padding: 2rem;
        margin: 1rem;
        border-radius: 1.5rem;
        background-color: #f0f2f6;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        transition: 0.3s ease-in-out;
    }
    .card:hover {
        background-color: #e0e0e0;
        transform: scale(1.03);
    }
    .card a {
        text-decoration: none;
        color: black;
    }
</style>
"""
st.markdown(card_style, unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        '<div class="card"><a href="?page=ask">📊<br><strong>Ask Questions<br>About Data</strong></a></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="card"><a href="?page=bestsellers">🔥<br><strong>Best Sellers</strong></a></div>',
        unsafe_allow_html=True,
    )

# Handle routing
query_params = st.experimental_get_query_params()
if "page" in query_params:
    page = query_params["page"][0]
    if page == "ask":
        switch_page("1_Ask_Questions")
    elif page == "bestsellers":
        switch_page("2_Best_Sellers")
