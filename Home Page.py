import streamlit as st

st.set_page_config("Marketplace Analyzer", layout="wide")

st.markdown("<h1 style='text-align: center;'>🕒 Welcome to the Watch Marketplace Analyzer</h1>", unsafe_allow_html=True)
st.markdown("### Use the options in the sidebar to explore:", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/1_Ask_Questions.py", label="📊 Ask Questions", icon="📊")

with col2:
    st.page_link("pages/2_Best_Sellers.py", label="🏆 View Best Sellers", icon="🏆")
