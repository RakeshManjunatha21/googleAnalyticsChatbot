# app.py
import os
import json
import streamlit as st
import pandas as pd
# from dotenv import load_dotenv
import google.generativeai as genai
from streamlit_chat import message

# ── LOAD SECRETS ───────────────────────────────────────────────────────────────
# load_dotenv()
GEMINI_API_KEY = "AIzaSyBIBr01u6_BNVfYk989DXkv3FKQA928Kq8"
genai.configure(api_key=GEMINI_API_KEY)

# ── GEMINI CALL WRAPPER ─────────────────────────────────────────────────────────
def gemini_response(prompt: str) -> str:
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.types.GenerationConfig(temperature=0.2)
    )
    resp = model.generate_content(prompt)
    # pick first candidate
    return (
        resp.candidates[0].content.parts[0].text
        if hasattr(resp, "candidates") else resp.text
    )

# ── LOAD GA4 EXCEL (all sheets) ────────────────────────────────────────────────
@st.cache_data
def load_all_sheets(path: str) -> dict:
    return pd.read_excel(path, sheet_name=None)

data = load_all_sheets("GA4_Full_Report_Apr2023_Mar2024_V4.xlsx")

# ── PREPARE SCHEMA + DATA JSON ─────────────────────────────────────────────────
# 1) Build simple sheet→columns summary
schema_info = []
for sheet, df in data.items():
    cols = df.columns.tolist()
    schema_info.append(f"• {sheet}: columns = {cols}")
schema_text = "\n".join(schema_info)

# 2) Convert entire dataset to JSON
#    (this can be large—ensure your deployment can handle it)
data_json = json.dumps(
    {sheet: df.to_dict(orient="records") for sheet, df in data.items()},
    indent=None
)

# ── STREAMLIT CHAT UI ─────────────────────────────────────────────────────────
# st.set_page_config(page_title="GA4 Full-Data Chat", layout="wide")
import streamlit as st
from streamlit.components.v1 import html

# Set page config

# Custom CSS for better UI
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .title {
            font-size: 2.8rem;
            font-weight: 600;
            color: #0f4c81;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #6c757d;
            margin-bottom: 2rem;
        }
        .stButton>button {
            border-radius: 10px;
            background-color: #0f4c81;
            color: white;
            font-weight: bold;
        }
        .stTextInput>div>div>input {
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown('<div class="title">💬 Google Analytics Chat Assistant</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Ask questions, get insights. Powered by Gemini AI & Google Analytics 4</div>', unsafe_allow_html=True)


if "history" not in st.session_state:
    st.session_state.history = []

# display existing history
for idx, (role, txt) in enumerate(st.session_state.history):
    message(txt, is_user=(role=="user"), key=f"msg_{role}_{idx}")

# get user input
query = st.chat_input("Ask any question about your Google Analytics…", key="input_1")
txt_file_path = "prompt.txt"
with open(txt_file_path, "r", encoding="utf-8") as file:
    data_text = file.read()



if query:
    # record user
    st.session_state.history.append(("user", query))
    message(query, is_user=True, key=f"msg_user_{len(st.session_state.history)}")

    # build the full prompt
    prompt = f"""
    You are an expert performance marketing analyst. Your role is to deliver precise, insight-driven answers to user questions using only the data provided. Your responses must reflect the depth, clarity, and strategic focus expected from a senior growth consultant or marketing strategist, with the goal of driving measurable business impact.

    Response Rules and Expectations:

    Only use the provided data.
    Avoid assumptions or generic advice. Every insight must be grounded in specific, interpretable patterns or metrics observed in the data.

    Engagement Rate Calculation (when relevant):
    If the question involves performance evaluation (e.g., landing pages or user engagement), calculate and report:

    Engagement Rate = (Engaged Sessions / Total Sessions) × 100
    URL Handling:
    If full links (URLs) are available in the data and relevant to the question:

    Always include the full URL in the output.

    You may use a short name for readability, but ensure the actual link is visible or hyperlinked appropriately.

    No reference to data structures.
    Do not mention terms like "columns", "rows", "JSON", "table", or "spreadsheet".

    Executive-facing tone and delivery:
    Write confidently and clearly, as if presenting to a CMO, senior marketing lead, or strategy team. Avoid technical explanations or raw data summaries without insight.

    Your response must include:

    Insight Summary:
    Present core findings using tables and bullet points for clarity. Highlight:

    Key metric comparisons

    Notable changes, trends, and patterns

    Data shifts that impact performance

    Performance Analysis:
    Identify and explain:

    What worked well (top-performing elements or strategies)

    What underperformed (inefficient or low-impact areas)

    What requires improvement (areas with optimization potential)

    Strategic Recommendations:
    Translate data insights into actionable recommendations. Focus on:

    ROI improvements

    Cost efficiency

    Funnel or conversion optimization

    Channel or content effectiveness

    Avoid:

    Generic or repetitive advice

    Metrics without interpretation

    Mentioning anything about the structure of the data (e.g., headers, keys, datasets)

    User Question:
    {query}

    Data to use (Google Ads - JSON):
    {data_text}

    """


    # get the model’s answer
    answer = gemini_response(prompt).strip()

    # record assistant
    st.session_state.history.append(("assistant", answer))
    message(answer, is_user=False, key=f"msg_assistant_{len(st.session_state.history)}")
