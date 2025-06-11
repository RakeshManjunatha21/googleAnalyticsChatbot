import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

st.set_page_config(page_title="Ads Intelligence Assistant", layout="wide")

# ─────────────────────────────────────────────────────
# CONFIGURE GEMINI
# ─────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyBIBr01u6_BNVfYk989DXkv3FKQA928Kq8"
genai.configure(api_key=GEMINI_API_KEY)

def gemini_response(prompt: str) -> str:
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config=genai.types.GenerationConfig(temperature=0.2)
    )
    resp = model.generate_content(prompt)
    return (
        resp.candidates[0].content.parts[0].text
        if hasattr(resp, "candidates") else resp.text
    )

# ─────────────────────────────────────────────────────
# LOAD JSON & EXCEL DATA
# ─────────────────────────────────────────────────────
@st.cache_data
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_excel(file_path):
    return pd.read_excel(file_path)

# Load all datasets
landing_data = load_json("combined_landing_pages.json")
campaign_data = load_json("campaign_report.json")
ad_asset_df = load_excel("Ad asset report.xlsx")
search_terms_df = load_excel("Search terms report.xlsx")
responsive_ads_df = load_excel("Responsive search ad combinations report.xlsx")
asset_detail_df = load_excel("ADR -Insurance Home page (Phrase Match).xlsx")
device_report_df = load_excel("Device report.xlsx")

# Dataset mapping
DATASETS = {
    "landing_data": landing_data,
    "campaign_data": campaign_data,
    "ad_asset_df": ad_asset_df,
    "search_terms_df": search_terms_df,
    "responsive_ads_df": responsive_ads_df,
    "asset_detail_df": asset_detail_df,
    "device_report_df": device_report_df
}

# ─────────────────────────────────────────────────────
# UI HEADER & STYLE
# ─────────────────────────────────────────────────────
st.markdown("""
    <style>
        .title {
            font-size: 2.7rem;
            font-weight: bold;
            color: #0b3c5d;
            margin-bottom: 0.3rem;
        }
        .subtitle {
            font-size: 1rem;
            color: #666;
            margin-bottom: 1.5rem;
        }
        .question-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }
        .question-card:hover {
            background: rgba(13, 110, 253, 0.08);
            cursor: pointer;
            transform: scale(1.01);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Ads Intelligence Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tap a question below or type your own query to explore ad performance insights</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# ─────────────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────────────
for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)

# ─────────────────────────────────────────────────────
# TOP 5 Suggested Questions (Related to Actual Data)
# ─────────────────────────────────────────────────────
def get_top_5_questions():
    return [
        "Which landing pages have high spend but low conversions?",
        "Which keywords from the search term report are underperforming?",
        "Which ad assets have low CTR and need replacement?",
        "How are responsive ads performing across devices?",
        "Which campaigns are getting clicks but no conversions?"
    ]

if len(st.session_state.history) == 0:
    suggested_questions = get_top_5_questions()
    cols = st.columns(2)
    for i, q in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(q, key=f"suggested_{i}"):
                st.session_state.selected_question = q

# ─────────────────────────────────────────────────────
# INPUT + DYNAMIC PROMPT GENERATION
# ─────────────────────────────────────────────────────
query = st.chat_input("Ask a performance question about your campaign data...")
active_query = query or st.session_state.selected_question

if active_query:
    st.chat_message("user").write(active_query)
    st.session_state.history.append(("user", active_query))
    st.session_state.selected_question = None

    # Determine which datasets are relevant to the question
    prompt_data_blocks = []
    if "landing" in active_query.lower():
        prompt_data_blocks.append(f"""**Landing Page Data:**\n{json.dumps(landing_data, indent=None)}""")
    if "keyword" in active_query.lower() or "search term" in active_query.lower():
        prompt_data_blocks.append(f"""**Search Terms Data:**\n{search_terms_df.head(100).to_markdown(index=False)}""")
    if "asset" in active_query.lower() or "creative" in active_query.lower():
        prompt_data_blocks.append(f"""**Ad Asset Report (top 100):**\n{ad_asset_df.head(100).to_markdown(index=False)}""")
    if "device" in active_query.lower():
        prompt_data_blocks.append(f"""**Device Report:**\n{device_report_df.head(50).to_markdown(index=False)}""")
    if "responsive" in active_query.lower():
        prompt_data_blocks.append(f"""**Responsive Ads Report:**\n{responsive_ads_df.head(100).to_markdown(index=False)}""")
    if "campaign" in active_query.lower():
        prompt_data_blocks.append(f"""**Campaign Report:**\n{json.dumps(campaign_data, indent=None)}""")

    prompt = f"""
You are a **Senior Google Ads Strategist**. Deliver clear, structured, and actionable insights.

Respond with:
1. Tables (impressions, clicks, cost/click, conversions, spend, engagement % and category).
2. Highlight underperformance and exact recommendations (e.g., remove X, add Y, shift budget to Z).
3. Provide clean summaries.

### User Query:
{active_query}

### Relevant Data:
{chr(10).join(prompt_data_blocks)}
"""

    response = gemini_response(prompt).strip()
    st.chat_message("assistant").write(response)
    st.session_state.history.append(("assistant", response))
