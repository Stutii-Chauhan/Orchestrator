
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
DB = st.secrets["SUPABASE_DB"]
USER = st.secrets["SUPABASE_USER"]
PASSWORD = quote_plus(st.secrets["SUPABASE_PASSWORD"])
HOST = st.secrets["SUPABASE_HOST"]
PORT = st.secrets["SUPABASE_PORT"]
connection_string = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
engine = create_engine(connection_string)

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
    # Table schema list as bullet points
    schema_desc = "\n".join([f"- {table}: [{', '.join(cols)}]" for table, cols in TABLE_SCHEMAS.items()])
    
    # Rules for selecting the correct table
    table_guidance = """
The tables contain watch data from Amazon across brands.

Refer to the user’s question and select the correct table using the rules below:

1. If the question mentions dominant brand/brands, product count, products per brand, number of products, total products, or products across price bands or buckets → use: `All - Product Count_output`
   Do NOT use `Top 1000 - Product Count_output` unless the question specifically mentions Top 1000.

2. If the question mentions SKU count, SKUs per brand, or total SKUs → use: `All - SKU Count_output`, or gender-specific variants if mentioned.

3. If the question contains "Top 1000" or refers to Amazon ranking → use: `Top 1000 - Product Count_output` or `Top 1000 - SKU Count_output`

4. For distribution of products across price ranges by gender:
   - Use `men_price_range_top100_output` for men
   - Use `women_price_range_top100_output` for women

5. If the question mentions best rank or first appearance → use: `Best Rank_All_output`

6. For gender-specific product details → use:
   - `Final_Watch_Dataset_Men_output` for men's watches
   - `Final_Watch_Dataset_Women_output` for women's watches

7. For general product listings, price, discount, or brand comparisons → use: `product_price_cleaned_output`

8. If the question includes subjective terms like “top brands”, “leading brands”, or “dominant brands”, assume dominance is based on **highest product count** → use: `All - Product Count_output`
   - Sort by `"10k–15k" + "15k–25k" + ...` if needed, or just use total sum

9. Always try to show the comparision factor, sum, total etc. along with the output
10. Avoid cases where Brand = "Others"
"""

    # Compose the full prompt to send to Gemini
    prompt = f"""
You are a SQL expert agent working with PostgreSQL.

Below are the available tables and their columns:
{schema_desc}

{table_guidance}

Now, based on the user's question below, choose the right table and generate the SQL query.

User Question: {user_query}

Only return the SQL query.
"""

    # Call Gemini to generate the SQL
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
st.set_page_config("Marketplace Analyzer", layout="wide")
st.title("Marketplace Analyzer")

user_question = st.text_input("Ask a question about your data:")

if user_question:
    with st.spinner("Generating SQL..."):
        sql_query = generate_sql(user_question)

    if sql_query.lower().startswith("invalid_query"):
        st.warning("Couldn't understand or match your question to a known table.")
        st.stop()

    clean_query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    st.code(clean_query, language="sql")

    if st.button("▶️ Run Query"):
        try:
            df = pd.read_sql_query(clean_query, engine)
            st.success("Query executed successfully!")
            st.dataframe(df)

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
