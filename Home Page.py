import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.switch_page_button import switch_page

# --- Page Setup ---
st.set_page_config(page_title="Login | Watch Marketplace Analyzer", page_icon="🔐", layout="centered")

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Login Logic ---
if not st.session_state.logged_in:
    st.title("🔐 Login to Marketplace Analyzer")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "titan123":
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Please login to access other features of the dashboard.")

# --- Redirect After Login ---
if st.session_state.logged_in:
    switch_page("Home Page")
