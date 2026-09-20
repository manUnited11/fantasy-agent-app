import os
import json
import requests
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION & DARK MODE STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Fantasy Football AI War Room",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e6ed; }
    .stMetric { background-color: #1e222d; padding: 12px; border-radius: 8px; border: 1px solid #2e3646; }
    .stChatMessage { border-radius: 8px; margin-bottom: 8px; }
    div[data-testid="stSidebar"] { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DRIVE DOCUMENT MAP & FETCH ENGINE
# -----------------------------------------------------------------------------
DOC_IDS = {
    "snapshot": "19dzRV44VHm5nVaj5ge8FEXaCGeqRZv7cw60CVKUq9iE",
    "hathat": "103a7PjQr5976ByVOOn3yR4aeoNI3mqABP4XtOTr5T2k",
    "bush": "10Q3y_nmdivTz0T1NECdhN8rFgoNDucGvO5zCITt-Ar4"
}
DOC_EXPORT_URL = "https://docs.google.com/document/d/{doc_id}/export?format=txt"

@st.cache_data(ttl=300)
def fetch_google_doc(doc_key: str) -> str:
    """Fetches text directly from Google Docs canvas synchronized via Apps Script."""
    if doc_key not in DOC_IDS:
        return ""
    url = DOC_EXPORT_URL.format(doc_id=DOC_IDS[doc_key])
    try:
        res = requests.get(url, timeout=10)
        return res.text if res.status_code == 200 else "Error loading document."
    except Exception as e:
        return f"Fetch error: {str(e)}"

def load_all_telemetry():
    return {
        "snapshot": fetch_google_doc("snapshot"),
        "hathat": fetch_google_doc("hathat"),
        "bush": fetch_google_doc("bush")
    }

# -----------------------------------------------------------------------------
# 3. MASTER STRATEGY SYSTEM PROMPT
# -----------------------------------------------------------------------------
MASTER_SYSTEM_PROMPT = """
You are an elite, highly intelligent Fantasy Football Management Agent and Strategy Advisor.
You manage two leagues for user 'manunited11':
1. Hat Hat Loop: 14-Team PPR, Scarcity Mode. High-Volume Touches (HVT = Targets + Red Zone Carries) and RB depth are paramount.
2. Bush League: 10-Team PPR, Optimization Mode. Churn low-ceiling bench depth for high explosive upside.

CORE STRATEGIC GUARDRAILS:
- Evaluate High-Volume Touches (HVT = Targets + RZ Carries, weighted 2.5x over standard carries).
- Apply Age Cliff Penalties: RB age >= 27 or WR age >= 31 face durability/volume penalties unless exempted by high HVT or route participation (>80%).
- Vegas Lines & Weather: Implied Team Totals >= 23.5 signal start-worthy offense. High wind (>= 15mph) penalizes pass-catchers and kickers.
- Positional Floor: Maintain a minimum 4-RB roster floor in 14-Team Scarcity Mode. Do NOT drop an active RB if it reduces total depth below 4.
- Hard Caps: Enforce 1 QB and 1 TE maximum active roster caps across all leagues.
- DST Streaming Rule: Target opposing offenses with Implied Totals <= 18.5, backup QBs, or injured offensive lines.
- Kicker Streaming Rule: Target dome games or low-wind outdoor games with team implied totals >= 23.5.

OUTPUT FORMAT REQUIREMENTS FOR ANALYSIS/WAIVER REQUESTS:
1. Executive Summary: 2-3 sentences on overall roster health and primary objective.
2. Detailed Analysis Table: Markdown table with (Target Add | Suggested Drop | Recommended Bid | Justification).
3. Priority Execution List: Numbered list in exact order of execution.
"""

# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Engine Settings")
    api_key_input = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
    
    if st.button("🔄 Sync Google Drive Telemetry"):
        st.cache_data.clear()
        st.success("Drive cache refreshed!")

    st.markdown("---")
    st.markdown("### 📊 Active Leagues")
    st.markdown("• **Hat Hat Loop** (14-Team Scarcity)")
    st.markdown("• **Bush League** (10-Team Optimization)")

# Retrieve telemetry context
telemetry = load_all_telemetry()

# -----------------------------------------------------------------------------
# 5. MAIN NAVIGATION TABS
# -----------------------------------------------------------------------------
st.title("🏈 Fantasy Football AI War Room")
st.caption("Live Google Drive Telemetry • Gemini 2.5/3.0 Flash • Google Search Grounded")

tab_chat, tab_compare, tab_lineup, tab_waivers, tab_trades, tab_data = st.tabs([
    "💬 AI Strategy Chat", 
    "⚖️ Player Compare", 
    "🛡️ Lineup & Streamers", 
    "🎯 Waiver Wire", 
    "🤝 Trade Calculator",
    "📄 Raw Telemetry"
])

# -----------------------------------------------------------------------------
# TAB 1: CONVERSATIONAL CHAT WITH GOOGLE SEARCH GROUNDING
# -----------------------------------------------------------------------------
with tab_chat:
    st.subheader("Conversational Strategy Agent")
    st.caption("Ask questions about injury reports, practice participation, or specific roster moves.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    user_query = st.chat_input("Ask your Fantasy Agent a question...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        if not api_key_input:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing telemetry & searching live web sources..."):
                    try:
                        client = genai.Client(api_key=api_key_input)
                        full_prompt = f"""
USER QUERY: {user_query}

CURRENT TELEMETRY CONTEXT:
{json.dumps(telemetry)}
"""
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=MASTER_SYSTEM_PROMPT,
                                tools=[{"google_search": {}}],
                                temperature=0.2
                            )
                        )
                        answer = response.text
                        st.markdown(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"Gemini API Error: {str(e)}")

# -----------------------------------------------------------------------------
# TAB 2: INTELLIGENT PLAYER COMPARISON ENGINE
# -----------------------------------------------------------------------------
with tab_compare:
    st.subheader("⚖️ Player Comparison Engine")
    col1, col2 = st.columns(2)
    with col1:
        p_a = st.text_input("Player A:", value="Jayden Reed")
    with col2:
        p_b = st.text_input("Player B:", value="Adonai Mitchell")
        
    if st.button("Compare Players with Grounded Analytics", type="primary"):
        if not api_key_input:
            st.error("Missing Gemini API Key.")
        else:
            with st.spinner(f"Comparing {p_a} vs {p_b}..."):
                client = genai.Client(api_key=api_key_input)
                prompt = f"""
Compare {p_a} vs {p_b} using usage metrics and Vegas game scripts.

TELEMETRY CONTEXT:
{telemetry['snapshot']}

Structure the comparison:
1. High-Value Touches (HVT = Targets + Red Zone Carries) & Target Share
2. Route Participation (%) and TPRR
3. Vegas Implied Team Total & Spread Context
4. Live Practice Status / Injury Check via Search
5. Final Recommendation & Verdict
"""
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=MASTER_SYSTEM_PROMPT,
                        tools=[{"google_search": {}}],
                        temperature=0.1
                    )
                )
                st.markdown(res.text)

# -----------------------------------------------------------------------------
# TAB 3: LINEUP & STREAMER OPTIMIZER (DEFENSE & KICKER)
# -----------------------------------------------------------------------------
with tab_lineup:
    st.subheader("🛡️ Lineup & Streamer Optimizer")
    selected_league_lineup = st.selectbox("Select League:", ["Hat Hat Loop (Scarcity)", "Bush League (Optimization)"])
    
    if st.button("Optimize Lineup & Find Streamers"):
        if not api_key_input:
            st.error("Missing Gemini API Key.")
        else:
            with st.spinner("Optimizing lineup and evaluating streamer targets..."):
                client = genai.Client(api_key=api_key_input)
                league_key = "hathat" if "Hat Hat" in selected_league_lineup else "bush"
                prompt = f"""
Provide optimal starting lineup for {selected_league_lineup}.
Include specific streaming targets for Defense (DST) and Kicker based on Vegas totals, OL injuries, and stadium weather.

ROSTER STATE:
{telemetry[league_key]}

TELEMETRY SNAPSHOT:
{telemetry['snapshot']}
"""
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=MASTER_SYSTEM_PROMPT,
                        tools=[{"google_search": {}}],
                        temperature=0.1
                    )
                )
                st.markdown(res.text)

# -----------------------------------------------------------------------------
# TAB 4: AUTOMATED WAIVER WIRE STRATEGY
# -----------------------------------------------------------------------------
with tab_waivers:
    st.subheader("🎯 Automated Waiver Wire Strategy")
    if st.button("Generate Waiver Wire Recommendations"):
        if not api_key_input:
            st.error("Missing Gemini API Key.")
        else:
            with st.spinner("Analyzing waiver options across both leagues..."):
                client = genai.Client(api_key=api_key_input)
                prompt = f"""
Generate full waiver wire recommendations for BOTH Hat Hat Loop (14-Team Scarcity) and Bush League (10-Team Optimization).

SNAPSHOT TELEMETRY:
{telemetry['snapshot']}

HAT HAT ROSTER:
{telemetry['hathat']}

BUSH ROSTER:
{telemetry['bush']}

Enforce the 3-part output format: Executive Summary, Detailed Analysis Table, Priority Execution List.
"""
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=MASTER_SYSTEM_PROMPT,
                        tools=[{"google_search": {}}],
                        temperature=0.1
                    )
                )
                st.markdown(res.text)

# -----------------------------------------------------------------------------
# TAB 5: TRADE CALCULATOR & PROPOSAL ENGINE
# -----------------------------------------------------------------------------
with tab_trades:
    st.subheader("🤝 Strategic Trade Engine")
    trade_league = st.selectbox("Select League:", ["Hat Hat Loop", "Bush League"], key="t_league")
    
    if st.button("Generate Strategic Trade Proposals"):
        if not api_key_input:
            st.error("Missing Gemini API Key.")
        else:
            with st.spinner("Analyzing roster depth for consolidation trades..."):
                client = genai.Client(api_key=api_key_input)
                league_key = "hathat" if "Hat Hat" in trade_league else "bush"
                prompt = f"""
Analyze {trade_league} roster and generate 3 strategic trade proposals.
Focus on 2-for-1 consolidation trades to free up bench space for waiver adds while maintaining Hero-RB floors.

ROSTER STATE:
{telemetry[league_key]}
"""
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=MASTER_SYSTEM_PROMPT,
                        temperature=0.2
                    )
                )
                st.markdown(res.text)

# -----------------------------------------------------------------------------
# TAB 6: RAW TELEMETRY VIEW
# -----------------------------------------------------------------------------
with tab_data:
    st.subheader("📄 Raw Google Drive Markdown Telemetry")
    t1, t2, t3 = st.tabs(["snapshot.md", "hathat.md", "bush.md"])
    with t1:
        st.markdown(telemetry["snapshot"])
    with t2:
        st.markdown(telemetry["hathat"])
    with t3:
        st.markdown(telemetry["bush"])
