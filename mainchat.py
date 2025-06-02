import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

st.set_page_config(page_title="💼 Ads Intelligence Assistant", layout="wide")

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

df = pd.read_excel("Ad asset report.xlsx")
campaign_data = load_json("campaign_report.json")
landing_data = load_json("combined_landing_pages.json")

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

st.markdown('<div class="title">💼 Ads Intelligence Assistant</div>', unsafe_allow_html=True)
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
# INITIAL SUGGESTIONS (First Interaction Only)
# ─────────────────────────────────────────────────────
if len(st.session_state.history) == 0:
    suggested_questions = [
        "Which landing pages are underperforming based on conversion rate?",
        "Which keywords are wasting budget with poor conversions?",
        "What ad creatives need improvement in CTR or relevance?",
        "Which campaigns have the best ROI and why?",
        "Suggest improvements for headline and CTA effectiveness"
    ]

    cols = st.columns(2)
    for i, q in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(q, key=f"suggested_{i}", help="Click to use this question"):
                st.session_state.selected_question = q

# ─────────────────────────────────────────────────────
# CHAT INPUT & MAIN LOGIC
# ─────────────────────────────────────────────────────
query = st.chat_input("Ask a performance question about your campaign data...")
active_query = query or st.session_state.selected_question

if active_query:
    st.chat_message("user").write(active_query)
    st.session_state.history.append(("user", active_query))
    st.session_state.selected_question = None

    prompt = f"""
You are a Senior Google Ads Strategist helping me analyze campaign and landing page performance.

• Speak in a confident, insightful tone—avoid robotic or overly formal language.
• Present insights using tables or bullet points when appropriate.
• Avoid phrases like “according to the data” or “from the report.”
• Focus on delivering clear, specific, and actionable recommendations that drive performance.
• Conclude each analysis with a natural follow-up question that builds on the current insights—something you'd want to validate or explore further to refine strategy.
• Do not ask open-ended questions like “Can you provide XYZ?”—instead, pose questions that assume access to data and ask for confirmation or clarification if needed (e.g., “Should we dig deeper into the top-performing keywords from this segment?”

USER QUESTION:
{active_query}

CAMPAIGN DATA:
{json.dumps(campaign_data, indent=None)}

LANDING PAGE DATA:
{json.dumps(landing_data, indent=None)}

ASSET REPORT (TOP 10 ROWS):
{df.head(10).to_markdown(index=False)}
"""

    response = gemini_response(prompt).strip()
    st.chat_message("assistant").write(response)
    st.session_state.history.append(("assistant", response))
