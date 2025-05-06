import streamlit as st
import pandas as pd
import google.generativeai as genai
from sqlalchemy import create_engine
import plotly.express as px
from urllib.parse import quote_plus

# ---- Gemini Setup ----
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# ---- Supabase Connection ----


# ---- Supabase Connection ----
# Correctly encode password for URL
DB = st.secrets["SUPABASE_DB"]
USER = st.secrets["SUPABASE_USER"]
PASSWORD = quote_plus(st.secrets["SUPABASE_PASSWORD"])  # Handles special chars like @ or !
HOST = st.secrets["SUPABASE_HOST"]
PORT = st.secrets["SUPABASE_PORT"]

# Create engine from formatted connection string
engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")


# ---- Table Metadata ----
TABLE_SCHEMAS = {
    "product_price_cleaned_output": ["product_url", "product_name", "product_price", "product_code", "brand"],
    "All - Product Count_output": ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "<10k"],
    "All - SKU Count_output": ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "<10k"],
    "Top 1000 - Product Count_output": ["brand", "Top 1000 Product Count"],
    "Top 1000 - SKU Count_output": ["brand", "Top 1000 SKU Count"],
    "Men - Product Count_output": ["brand", "Men - Product Count"],
    "Men - SKU Count_output": ["brand", "Men - SKU Count"],
    "Women - Product Count_output": ["brand", "Women - Product Count"],
    "Women - SKU Count_output": ["brand", "Women - SKU Count"],
    "Best Rank_All_output": ["brand", "Best Rank (First Appearance)"],
    "men_price_range_top100_output": ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "total"],
    "women_price_range_top100_output": ["brand", "10k–15k", "15k–25k", "25k–40k", "40k+", "total"],
    "Final_Watch_Dataset_Men_output": ["URL", "Brand", "Product Name", "Model Number", "Price", "Ratings", "Discount", "Band Colour", "Band Material", "Band Width", "Case Diameter", "Case Material", "Case Thickness", "Dial Colour", "Crystal Material", "Case Shape", "Movement", "Water Resistance Depth", "Special Features", "ImageURL"],
    "Final_Watch_Dataset_Women_output": ["URL", "Brand", "Product Name", "Model Number", "Price", "Ratings", "Discount", "Band Colour", "Band Material", "Band Width", "Case Diameter", "Case Material", "Case Thickness", "Dial Colour", "Crystal Material", "Case Shape", "Movement", "Water Resistance Depth", "Special Features", "ImageURL"]
}

# ---- LLM SQL Generator ----
def generate_sql(user_query):
    schema_desc = "\n".join([f"- {table}: [{', '.join(cols)}]" for table, cols in TABLE_SCHEMAS.items()])
    prompt = f"""
You are a SQL expert. Use the correct table based on the question.

Available Tables and Columns:
{schema_desc}

Instructions:
- Return ONLY the SQL query.
- DO NOT explain.
- If unclear, return exactly: INVALID_QUERY

User: {user_query}

SQL Query:
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini failed: {e}"

# ---- Visualization Type ----
def infer_chart_type(query):
    prompt = f"""
Suggest a chart type (bar, pie, line, scatter, none) to visualize the result of this question:

"{query}"

Answer only with the chart type, no explanation.
"""
    try:
        result = model.generate_content(prompt).text.strip().lower()
        return result if result in ["bar", "pie", "line", "scatter"] else "none"
    except:
        return "none"

# ---- Streamlit UI ----
st.set_page_config("Supabase Data Explorer with Gemini", layout="wide")
st.title("🔍 Supabase Data Explorer with Gemini")

user_question = st.text_input("Ask a question about your data:")

if user_question:
    with st.spinner("Generating SQL..."):
        sql_query = generate_sql(user_question)

    if sql_query.lower().startswith("invalid_query"):
        st.warning("Couldn't understand or match your question to a known table.")
        st.stop()

    st.code(sql_query, language="sql")

    if st.button("▶️ Run Query"):
        try:
            df = pd.read_sql_query(sql_query, engine)
            st.success("Query executed successfully!")
            st.dataframe(df)

            # ---- Chart ----
            if not df.empty:
                chart_type = infer_chart_type(user_question)
                if chart_type == "bar":
                    st.bar_chart(df.set_index(df.columns[0]))
                elif chart_type == "line":
                    st.line_chart(df.set_index(df.columns[0]))
                elif chart_type == "pie" and df.shape[1] >= 2:
                    fig = px.pie(df, names=df.columns[0], values=df.columns[1])
                    st.plotly_chart(fig)
                elif chart_type == "scatter" and df.shape[1] >= 2:
                    fig = px.scatter(df, x=df.columns[0], y=df.columns[1])
                    st.plotly_chart(fig)

        except Exception as e:
            st.error(f"Query failed: {e}")
