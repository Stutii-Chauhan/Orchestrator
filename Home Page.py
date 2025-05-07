import streamlit as st

# ------------------------
# Session Setup
# ------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "Login"

# ------------------------
# Sidebar Navigation
# ------------------------
st.sidebar.title("Navigation")
if st.sidebar.button("Home Page"):
    st.session_state.page = "Login"

# Disable other buttons if not logged in
disabled = not st.session_state.authenticated
if st.sidebar.button("Ask Questions", disabled=disabled):
    st.session_state.page = "Ask Questions"
if st.sidebar.button("Best Sellers", disabled=disabled):
    st.session_state.page = "Best Sellers"

# ------------------------
# Login Page
# ------------------------
def show_login():
    st.title("🔐 Login to Marketplace Analyzer")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "pass":
            st.session_state.authenticated = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ------------------------
# Ask Questions Page
# ------------------------
def show_questions():
    st.title("📊 Ask Questions About Your Data")
    st.info("This is where your Gemini-powered data Q&A would go.")

# ------------------------
# Best Sellers Page
# ------------------------
def show_best_sellers():
    st.title("🏆 Best Selling Watches")
    st.info("This is where your brand filters and best seller listings would appear.")

# ------------------------
# Page Router
# ------------------------
if st.session_state.page == "Login":
    show_login()
elif st.session_state.page == "Ask Questions":
    show_questions()
elif st.session_state.page == "Best Sellers":
    show_best_sellers()
