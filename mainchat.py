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
st.title("💬 Google Analytics Chat Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

# display existing history
for idx, (role, txt) in enumerate(st.session_state.history):
    message(txt, is_user=(role=="user"), key=f"msg_{role}_{idx}")

# get user input
query = st.chat_input("Ask any question about your Google Analytics…", key="input_1")
json_file_path = "combined_data_mod_v2.json"
with open(json_file_path, "r", encoding="utf-8") as f:
    data_loaded_adward = json.load(f)


if query:
    # record user
    st.session_state.history.append(("user", query))
    message(query, is_user=True, key=f"msg_user_{len(st.session_state.history)}")

    # build the full prompt
    prompt = f"""

    Your role is to deliver precise, actionable, and insight-rich answers to the user's questions, using only the data provided.
    Approach each response like a seasoned growth consultant or performance marketer—capable of transforming data into strategic decisions, optimization opportunities, and business growth levers.

    🧠 Response Guidelines:
    Always root your analysis in the provided data, but do not expose or mention sheet names, column headers, or JSON keys.

    Prioritize business outcomes, not raw metrics. Avoid technical or structural explanations.

    Your tone should be confident, executive-facing, and conversational, as if presenting to a CMO, marketing lead, or strategy team.

    📌 Your response must always include:
    Data-driven insights in a clear tabular format – Compare key metrics, highlight patterns, and summarize findings visually when appropriate.

    Practical recommendations – Identify:

    What worked well (strengths to double down on),

    What didn’t (underperforming areas to rework), and

    What needs improvement (clear optimization paths).

    Strategic takeaways – Every insight should lead to a business-relevant recommendation. Think: cost efficiency, ROI impact, channel effectiveness, funnel improvements, etc.

    Use specific data points and relative comparisons to justify conclusions (e.g., uplift %, cost changes, engagement delta) without referencing source structures.

    ❌ Avoid:
    Generic commentary or restating metrics without interpretation.

    Mentioning “the dataset,” “the spreadsheet,” “the table,” or any structural elements

    ---

    **User Question:**  
    {query}

    **Data to use (Google Ads - JSON):**  
    {data_loaded_adward}
    """


    # get the model’s answer
    answer = gemini_response(prompt).strip()

    # record assistant
    st.session_state.history.append(("assistant", answer))
    message(answer, is_user=False, key=f"msg_assistant_{len(st.session_state.history)}")
