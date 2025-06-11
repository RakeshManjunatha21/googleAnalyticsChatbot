import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

st.set_page_config(page_title="Ads Intelligence Assistant", layout="wide")

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

@st.cache_data
def load_json(path): return json.load(open(path, "r", encoding="utf-8"))

@st.cache_data
def load_excel(path): return pd.read_excel(path)

# Load all datasets
landing_data = load_json("combined_landing_pages.json")
campaign_data = load_json("campaign_report.json")
ad_asset_df = load_excel("Ad asset report.xlsx")
search_terms_df = load_excel("Search terms report.xlsx")
responsive_ads_df = load_excel("Responsive search ad combinations report.xlsx")
asset_detail_df = load_excel("ADR -Insurance Home page (Phrase Match).xlsx")
device_report_df = load_excel("Device report.xlsx")

# ─────────────────────────────────────
# UI HEADER & STYLING
# ─────────────────────────────────────
st.markdown("""
<style>
.title { font-size: 2.7rem; font-weight: bold; color: #0b3c5d; }
.subtitle { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Ads Intelligence Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tap a question below or ask your own</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────
for key in ["history", "selected_question", "pending_followup"]:
    if key not in st.session_state: st.session_state[key] = None if key != "history" else []

# ─────────────────────────────────────
# SUGGESTED QUESTIONS
# ─────────────────────────────────────

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

# ─────────────────────────────────────
# HANDLE USER INPUT
# ─────────────────────────────────────
query = st.chat_input("Ask your campaign data question...")
active_query = query or st.session_state.selected_question

if active_query:
    st.chat_message("user").write(active_query)
    st.session_state.history.append(("user", active_query))
    st.session_state.selected_question = None

    prompt_data_blocks = []
    def summarize(df, label, top=10):
        prompt_data_blocks.append(f"**{label} (Top {top} rows shown):**\n{df.head(top).to_markdown(index=False)}")
        prompt_data_blocks.append("**NOTE:** Only showing top rows to keep response concise. Summarize actions based on full data.")

    if "landing" in active_query.lower():
        prompt_data_blocks.append(f"**Landing Page Data:**\n{json.dumps(landing_data)}")
    if "keyword" in active_query.lower() or "search term" in active_query.lower():
        summarize(search_terms_df, "Search Terms")
    if "asset" in active_query.lower() or "creative" in active_query.lower():
        summarize(ad_asset_df, "Ad Asset Report")
    if "device" in active_query.lower():
        summarize(device_report_df, "Device Report")
    if "responsive" in active_query.lower():
        summarize(responsive_ads_df, "Responsive Ads Report")
    if "campaign" in active_query.lower():
        prompt_data_blocks.append(f"**Campaign Report:**\n{json.dumps(campaign_data)}")

    # Final Prompt
    prompt = f"""
You are a **Senior Google Ads Strategist**.analyzing and Provide direct, actionable insights.

### Rules:
- No hypotheticals or vague advice.
- Use imperative tone: Add, Pause, Shift budget, Remove.
- Never ask for data or suggest checking anything.
- Condense large data into key takeaways.
- Follow-up must be a **single clear question** to drill deeper.
- Tables (impressions, clicks, cost/click, conversions, spend, engagement % and category).
- Highlight underperformance and exact recommendations (e.g., remove X, add Y, shift budget to Z).
- Provide clean summaries.

* Don’t speak in hypotheticals or ask the user to take action.
   * Instead, provide specific instructions:

     * *“Add the following high-performing keywords to campaign X: \[list].”*
     * *“Pause the following low-performing keywords due to poor engagement: \[list].”*

5. **Never ask the user to provide data.**

   * Avoid phrases like “please upload” or “can you provide”.
   * You may ask **validation-style follow-ups**, such as:
     *“Should we shift budget to Landing Page A based on its strong performance with high-converting keywords?”*

6. give budget recommendations based on performance data.

### User Query:
{active_query}

### Relevant Data:
{chr(10).join(prompt_data_blocks)}
"""

    # Response
    response = gemini_response(prompt).strip()
    st.chat_message("assistant").write(response)
    st.session_state.history.append(("assistant", response))
    st.session_state.pending_followup = "What would you like to drill down on next?"

# ─────────────────────────────────────
# FOLLOW-UP FLOW
# ─────────────────────────────────────
# if st.session_state.pending_followup:
#     followup = st.chat_input("Next Step: (Ask follow-up based on insights)")
#     if followup:
#         st.session_state.selected_question = followup
#         st.session_state.pending_followup = None
