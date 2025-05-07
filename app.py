import streamlit as st

st.set_page_config(page_title="Watch Marketplace Home", layout="centered")

st.title("⌚ Welcome to the Watch Marketplace Analyzer")
st.markdown("Use the options below to explore:")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Ask Questions"):
        st.switch_page("pages/1_Ask_Questions.py")

with col2:
    if st.button("🏆 View Best Sellers"):
        st.switch_page("pages/2_Best_Sellers.py")
