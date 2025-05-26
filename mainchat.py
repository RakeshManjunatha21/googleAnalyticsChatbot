import streamlit as st
import google.generativeai as genai
import json
import os
st.set_page_config(page_title="💼 ADs Intelligence Assistant", layout="wide")
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
# LOAD JSON DATA
# ─────────────────────────────────────────────────────
@st.cache_data
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

campaign_data = load_json("campaign_report.json")
landing_data = load_json("combined_landing_pages.json")

# ─────────────────────────────────────────────────────
# PAGE DESIGN
# ─────────────────────────────────────────────────────


st.markdown("""
    <style>
        .title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #0b3c5d;
            margin-top: 10px;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            font-size: 1.1rem;
            color: #6c757d;
            margin-bottom: 2rem;
        }
        .stChatMessage {
            padding: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💼 ADs Intelligence Assistant</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Campaign-related questions.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# SESSION HISTORY
# ─────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ─────────────────────────────────────────────────────
# RENDER HISTORY
# ─────────────────────────────────────────────────────
for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)

# ─────────────────────────────────────────────────────
# USER INPUT
# ─────────────────────────────────────────────────────
query = st.chat_input("Ask a performance question about your campaign data...")

if query:
    st.chat_message("user").write(query)
    st.session_state.history.append(("user", query))

    # ─────────────────────────────────────────────────
    # BUILD PROMPT
    # ─────────────────────────────────────────────────
    prompt = f"""
    You are a Google Ads performance strategist.

    You are a Senior Google Ads Marketing Strategist. Analyze the campaign and landing page performance data with precision and deliver clear, structured insights.

    Your responsibilities:

    Keyword-to-Landing Page Analysis

    For each landing page, identify associated keywords.

    Determine which keywords are performing best (based on traffic, engagement rate, and low bounce rate).

    Highlight which keywords are underperforming with clear data-backed reasons (e.g., high bounce rate, low CTR, poor conversion).

    For each keyword, explain why it works or doesn't, using actual metrics like CTR, engagement, clicks, conversions, and bounce rate.

    Recommendations & Strategy

    For underperforming keywords, provide specific actionable suggestions:

    How to improve ad copy, targeting, or landing page UX.

    Alternative high-potential keywords with better intent match.

    Headline, CTA, or content improvements based on user behavior.

    Provide keyword expansion suggestions using patterns in successful keywords.

    Recommend budget adjustments for high-ROI opportunities.

    Output Format

    Present the insights in a clean, structured format:

    Group by Landing Page → Keywords

    Include for each keyword: CTR, Clicks, Engagement Rate, Bounce Rate, and Conversion Rate

    Add a section: Why This Keyword Works / Doesn’t Work

    Add a section: Recommendation / Action Plan

    🔍 Important: Base all insights and recommendations strictly on the provided data. Avoid generic suggestions. Do not use phrases like “According to the data” or “From the report.” Keep the tone professional, insightful, and direct.

    USER QUERY:
    {query}

    CAMPAIGN DATA:
    {json.dumps(campaign_data, indent=None)}

    LANDING PAGE DATA:
    {json.dumps(landing_data, indent=None)}
    """

    # ─────────────────────────────────────────────────
    # GENERATE RESPONSE
    # ─────────────────────────────────────────────────
    response = gemini_response(prompt).strip()

    st.chat_message("assistant").write(response)
    st.session_state.history.append(("assistant", response))
