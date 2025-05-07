import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Watch Marketplace Analyzer",
    layout="centered",
    initial_sidebar_state="collapsed"  # 🔒 Hides the sidebar
)

# --- MAIN CONTENT ---
st.markdown("<h1 style='text-align: center;'>⌚ Welcome to the Watch Marketplace Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Use the options below to explore:</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.page_link("pages/1_Ask_Questions.py", label="📊 Ask Questions", icon="📈")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.page_link("pages/2_Best_Sellers.py", label="🏆 View Best Sellers", icon="🔥")
    st.markdown("</div>", unsafe_allow_html=True)
