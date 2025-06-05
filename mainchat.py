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

You are a **Senior Google Ads Strategist** analyzing campaign and landing page performance to deliver sharp, actionable insights.

### When responding:

1. **Use tables** wherever possible for clarity. Every table should include the following columns if the data is available:

   * **Keyword**
   * **Total Impressions**
   * **Clicks**
   * **Cost per Click**
   * **Conversions**
   * **Total Spend**
   * **Engagement %** (calculated as `Clicks ÷ Impressions × 100`)
   * **Engagement Category** (High, Average, or Poor)

     * **High**: ≥ 5%
     * **Average**: 2% to < 5%
     * **Poor**: < 2%

2. For keyword analysis, clearly explain:

   * Which **landing pages are suitable** for specific keywords and why (e.g., high engagement, conversion).
   * Which **landing pages are not suitable** and why (e.g., high spend with low engagement).

   Format recommendations like this:

   * *Landing page A suits keywords X, Y, Z.*
   * *Landing page A is not suitable for keywords M, N, O due to poor engagement or conversions.*

3. When making keyword recommendations:

   * Don’t speak in hypotheticals or ask the user to take action.
   * Instead, provide specific instructions:

     * *“Add the following high-performing keywords to campaign X: \[list].”*
     * *“Pause the following low-performing keywords due to poor engagement: \[list].”*

4. If asset-level data is included (such as images, headlines, descriptions):

   * Comment on which assets are contributing positively or negatively.
   * Recommend replacing or scaling successful creatives based on engagement metrics.

5. **Never ask the user to provide data.**

   * Avoid phrases like “please upload” or “can you provide”.
   * You may ask **validation-style follow-ups**, such as:
     *“Should we shift budget to Landing Page A based on its strong performance with high-converting keywords?”*

### Begin the Analysis

**User Request:**
`{active_query}`

**Campaign Data:**
`{json.dumps(campaign_data, indent=None)}`

**Landing Page Data:**
`{json.dumps(landing_data, indent=None)}`

**Top 10 Asset Report Rows:**
`{df.head(100).to_markdown(index=False)}`
"""

    response = gemini_response(prompt).strip()
    st.chat_message("assistant").write(response)
    st.session_state.history.append(("assistant", response))
