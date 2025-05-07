import streamlit as st
from streamlit_extras.switch_page_button import switch_page

# ---- Simple Login ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Login to Marketplace Analyzer")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "titan123":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    st.stop()

# ---- Main Home Page ----
st.set_page_config("Watch Marketplace Analyzer", layout="centered")

st.markdown("## ⌚ Welcome to the Watch Marketplace Analyzer")
st.markdown(
    "This platform helps you analyze the watch market by answering data-driven questions "
    "and exploring the top-selling analog watches across brands and price bands."
)
st.markdown("Use the options below to explore:")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Ask Questions"):
        switch_page("Ask Questions")

with col2:
    if st.button("🏆 View Best Sellers"):
        switch_page("Best Sellers")
