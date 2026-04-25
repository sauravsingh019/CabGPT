"""
=============================================================
  Agentic AI Cab Booking & Pricing Assistant
  Author: AI Engineering Demo
  Description: Multi-step agentic pipeline for cab booking
=============================================================
"""

import streamlit as st
import google.generativeai as genai
import json
import re
import time
import os
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CabGPT – AI Booking Assistant",
    page_icon="🚕",
    layout="centered",
)

# ─────────────────────────────────────────────
# CUSTOM CSS  (dark, sleek, production-grade UI)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    background: #0d0f14;
    color: #e8eaf0;
}

/* ── Header ── */
.cab-header {
    text-align: center;
    padding: 2rem 0 1rem;
}
.cab-header h1 {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f5c842 0%, #f08533 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}
.cab-header p {
    color: #7a7f94;
    font-size: 0.95rem;
    margin: 0;
}

/* ── Agent step cards ── */
.agent-step {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 0.85rem;
    animation: fadeSlide 0.35s ease forwards;
}
.step-done   { background: #1a2a1a; border-left: 3px solid #4caf50; }
.step-active { background: #1e1e2e; border-left: 3px solid #f5c842; }
.step-wait   { background: #141620; border-left: 3px solid #2e3145; color: #555; }

.step-icon { font-size: 1.1rem; flex-shrink: 0; }
.step-label { font-weight: 600; color: #cdd0df; }
.step-detail { color: #888; font-size: 0.78rem; margin-top: 2px; font-family: 'JetBrains Mono', monospace; }

/* ── Result card ── */
.result-card {
    background: linear-gradient(145deg, #1a1d2e, #141620);
    border: 1px solid #2a2d40;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin: 1.2rem 0;
}
.result-card h3 {
    color: #f5c842;
    font-size: 1.1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.result-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #1e2136;
    font-size: 0.88rem;
}
.result-row:last-child { border-bottom: none; }
.result-label { color: #7a7f94; }
.result-value { color: #e8eaf0; font-weight: 600; }

/* ── Cab type badge ── */
.cab-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-mini  { background: #1e2f1e; color: #6fcf6f; border: 1px solid #4caf50; }
.badge-sedan { background: #1e2040; color: #7eb8f5; border: 1px solid #4a90d9; }
.badge-suv   { background: #2a1e10; color: #f5a742; border: 1px solid #e08030; }

/* ── Fare highlight ── */
.fare-highlight {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(135deg, #1e1a08, #2a2210);
    border: 1px solid #4a3a10;
    border-radius: 12px;
    margin-top: 1rem;
}
.fare-amount {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f5c842;
    font-family: 'JetBrains Mono', monospace;
}
.fare-label { color: #7a7f94; font-size: 0.8rem; margin-top: 4px; }

/* ── Sample prompts ── */
.sample-btn-wrapper { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.8rem 0 1.2rem; }

/* ── Chat bubbles ── */
.user-msg {
    background: #1e2136;
    border: 1px solid #2e3255;
    border-radius: 14px 14px 4px 14px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.9rem;
    color: #e8eaf0;
    max-width: 90%;
    margin-left: auto;
}
.bot-msg {
    background: #141a1e;
    border: 1px solid #1e2a30;
    border-radius: 14px 14px 14px 4px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.9rem;
    color: #9ab5c8;
    max-width: 90%;
}

/* ── Error / warn box ── */
.warn-box {
    background: #1e1010;
    border: 1px solid #8b2020;
    border-radius: 10px;
    padding: 12px 16px;
    color: #f08080;
    font-size: 0.85rem;
    margin: 0.8rem 0;
}

@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="cab-header">
    <h1>🚕 CabGPT</h1>
    <p>Agentic AI · Cab Booking &amp; Fare Estimation Assistant</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR – API KEY INPUT
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get your free key at https://makersuite.google.com/app/apikey"
    )
    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline")
    st.markdown("""
1. **NLP Agent** – extracts trip details  
2. **Distance Tool** – estimates km  
3. **Pricing Tool** – calculates fare  
4. **Decision Agent** – picks cab type  
5. **Response Agent** – formats output
    """)
    st.markdown("---")
    st.markdown("### 📍 Supported Cities")
    st.markdown("Meerut · Delhi · Noida · Gurgaon · Faridabad · Ghaziabad · Agra · Jaipur · Lucknow · Chandigarh")

# ─────────────────────────────────────────────
# RESOLVE API KEY  (env var or sidebar input)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or api_key_input.strip()

# ═════════════════════════════════════════════
# AGENT 1 – NLP EXTRACTION AGENT
# Uses Gemini to extract structured trip info
# ═════════════════════════════════════════════
def nlp_extraction_agent(user_message: str, api_key: str) -> dict:
    """
    AGENT 1 – NLP Extraction
    Sends the raw user message to Gemini and asks it to extract
    structured fields: pickup, drop, date, time.
    Returns a dict (or raises on failure).
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    today = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"""
You are a trip detail extraction agent. Today is {today}.

Extract the following fields from the user's cab booking request:
- pickup: pickup location (city/area name, string)
- drop: drop/destination location (city/area name, string)
- date: travel date in YYYY-MM-DD format (infer "today"/"tomorrow" from today's date)
- time: travel time in HH:MM 24h format (e.g. 09:00, 17:30)

User message: "{user_message}"

Respond ONLY with a valid JSON object. No explanation, no markdown fences, no extra text.
Example: {{"pickup": "Meerut", "drop": "Delhi", "date": "2025-07-15", "time": "09:00"}}

If a field cannot be determined, set it to null.
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if model adds them despite instructions
    raw = re.sub(r"```json|```", "", raw).strip()

    data = json.loads(raw)  # Raises json.JSONDecodeError if bad output
    return data


# ═════════════════════════════════════════════
# TOOL 2 – DISTANCE ESTIMATION TOOL
# Simple lookup table + symmetric fallback
# ═════════════════════════════════════════════

# Distance matrix (km) — bidirectional
DISTANCE_TABLE = {
    ("meerut",    "delhi"):      70,
    ("meerut",    "noida"):      60,
    ("meerut",    "gurgaon"):    95,
    ("meerut",    "faridabad"):  85,
    ("meerut",    "ghaziabad"):  35,
    ("meerut",    "agra"):       180,
    ("meerut",    "jaipur"):     320,
    ("meerut",    "lucknow"):    450,
    ("meerut",    "chandigarh"): 230,
    ("delhi",     "noida"):      20,
    ("delhi",     "gurgaon"):    30,
    ("delhi",     "faridabad"):  28,
    ("delhi",     "ghaziabad"):  25,
    ("delhi",     "agra"):       210,
    ("delhi",     "jaipur"):     270,
    ("delhi",     "lucknow"):    550,
    ("delhi",     "chandigarh"): 250,
    ("noida",     "gurgaon"):    45,
    ("noida",     "faridabad"):  35,
    ("noida",     "ghaziabad"):  15,
    ("noida",     "agra"):       165,
    ("noida",     "jaipur"):     220,
    ("gurgaon",   "faridabad"):  40,
    ("gurgaon",   "agra"):       200,
    ("gurgaon",   "jaipur"):     250,
    ("agra",      "jaipur"):     240,
    ("agra",      "lucknow"):    340,
    ("jaipur",    "lucknow"):    580,
    ("chandigarh","delhi"):      250,
}

def distance_tool(pickup: str, drop: str) -> float | None:
    """
    TOOL 2 – Distance Estimation
    Looks up distance from the table (case-insensitive, both directions).
    Returns distance in km, or None if route not found.
    """
    p = pickup.lower().strip()
    d = drop.lower().strip()

    if p == d:
        return 0.0

    return (
        DISTANCE_TABLE.get((p, d)) or
        DISTANCE_TABLE.get((d, p)) or
        None
    )


# ═════════════════════════════════════════════
# TOOL 3 – PRICING TOOL
# Applies fare rules and peak-hour multiplier
# ═════════════════════════════════════════════

CAB_RATES = {
    "Mini":  10,   # ₹ per km
    "Sedan": 15,
    "SUV":   20,
}
BASE_FARE     = 50   # ₹ flat charge
PEAK_MULTIPLIER = 1.2

# Peak hours: 8–11 AM  and  17–21 (5–9 PM)
PEAK_WINDOWS = [(8, 11), (17, 21)]

def is_peak_hour(time_str: str) -> bool:
    """Returns True if given HH:MM falls in peak hours."""
    if not time_str:
        return False
    try:
        h, m = map(int, time_str.split(":"))
        for (start, end) in PEAK_WINDOWS:
            if start <= h < end:
                return True
    except Exception:
        pass
    return False

def pricing_tool(distance_km: float, cab_type: str, time_str: str) -> dict:
    """
    TOOL 3 – Pricing Calculator
    Returns a breakdown dict with base_fare, distance_charge, multiplier, total.
    """
    rate           = CAB_RATES[cab_type]
    distance_charge = round(distance_km * rate, 2)
    subtotal        = BASE_FARE + distance_charge
    peak            = is_peak_hour(time_str)
    multiplier      = PEAK_MULTIPLIER if peak else 1.0
    total           = round(subtotal * multiplier, 2)

    return {
        "cab_type":        cab_type,
        "base_fare":       BASE_FARE,
        "distance_charge": distance_charge,
        "peak_hour":       peak,
        "multiplier":      multiplier,
        "total_fare":      total,
    }


# ═════════════════════════════════════════════
# AGENT 4 – DECISION AGENT
# Picks optimal cab type based on distance
# ═════════════════════════════════════════════

def decision_agent(distance_km: float) -> str:
    """
    AGENT 4 – Decision Agent
    Business logic for cab recommendation:
      < 5 km  → Mini
      5–15 km → Sedan
      ≥ 15 km → SUV
    """
    if distance_km < 5:
        return "Mini"
    elif distance_km <= 15:
        return "Sedan"
    else:
        return "SUV"


# ═════════════════════════════════════════════
# AGENT 5 – MASTER ORCHESTRATOR
# Runs the full agentic pipeline with live UI updates
# ═════════════════════════════════════════════

def run_agentic_pipeline(user_message: str, api_key: str):
    """
    MASTER ORCHESTRATOR – runs all agents in sequence,
    renders step-by-step progress, and returns final result.
    """

    # ── Containers for live updates ──
    steps_placeholder = st.empty()
    result_placeholder = st.empty()

    def render_steps(states: list[dict]):
        """Renders the agent pipeline steps live."""
        html = ""
        for s in states:
            cls  = {"done": "step-done", "active": "step-active", "wait": "step-wait"}[s["state"]]
            html += f"""
            <div class="agent-step {cls}">
                <span class="step-icon">{s['icon']}</span>
                <div>
                    <div class="step-label">{s['label']}</div>
                    <div class="step-detail">{s.get('detail','')}</div>
                </div>
            </div>"""
        steps_placeholder.markdown(html, unsafe_allow_html=True)

    # Initial state
    steps = [
        {"icon": "🧠", "label": "Agent 1 · NLP Extraction",   "state": "active", "detail": "Sending to Gemini..."},
        {"icon": "📏", "label": "Tool 2 · Distance Estimator", "state": "wait",   "detail": ""},
        {"icon": "💰", "label": "Tool 3 · Pricing Engine",     "state": "wait",   "detail": ""},
        {"icon": "🤖", "label": "Agent 4 · Decision Agent",    "state": "wait",   "detail": ""},
        {"icon": "✅", "label": "Agent 5 · Response Builder",  "state": "wait",   "detail": ""},
    ]
    render_steps(steps)

    # ── STEP 1: NLP EXTRACTION ──────────────────
    try:
        trip = nlp_extraction_agent(user_message, api_key)
    except json.JSONDecodeError:
        result_placeholder.markdown(
            '<div class="warn-box">⚠️ AI returned unexpected output. Please rephrase your request.</div>',
            unsafe_allow_html=True
        )
        steps_placeholder.empty()
        return
    except Exception as e:
        result_placeholder.markdown(
            f'<div class="warn-box">⚠️ API Error: {e}<br><br>Check your Gemini API key in the sidebar.</div>',
            unsafe_allow_html=True
        )
        steps_placeholder.empty()
        return

    # Validate required fields
    missing = [f for f in ["pickup", "drop", "date", "time"] if not trip.get(f)]
    if missing:
        result_placeholder.markdown(
            f'<div class="warn-box">⚠️ Could not extract: <b>{", ".join(missing)}</b>.<br>'
            f'Please include all trip details (pickup, destination, date, time).</div>',
            unsafe_allow_html=True
        )
        steps_placeholder.empty()
        return

    steps[0]["state"]  = "done"
    steps[0]["detail"] = f'{trip["pickup"]} → {trip["drop"]}  |  {trip["date"]}  {trip["time"]}'
    steps[1]["state"]  = "active"
    steps[1]["detail"] = "Looking up route distance..."
    render_steps(steps)
    time.sleep(0.4)

    # ── STEP 2: DISTANCE TOOL ───────────────────
    distance = distance_tool(trip["pickup"], trip["drop"])
    if distance is None:
        result_placeholder.markdown(
            f'<div class="warn-box">⚠️ Route not found: <b>{trip["pickup"]}</b> → <b>{trip["drop"]}</b>.<br>'
            f'Try cities like Meerut, Delhi, Noida, Gurgaon, Agra, Jaipur, Lucknow, Chandigarh.</div>',
            unsafe_allow_html=True
        )
        steps_placeholder.empty()
        return

    steps[1]["state"]  = "done"
    steps[1]["detail"] = f'{distance} km estimated'
    steps[2]["state"]  = "active"
    steps[2]["detail"] = "Computing fares for all cab types..."
    render_steps(steps)
    time.sleep(0.3)

    # ── STEP 3: DECISION AGENT ──────────────────
    cab_type = decision_agent(distance)

    steps[2]["state"]  = "done"
    steps[2]["detail"] = f'Recommended: {cab_type}'
    steps[3]["state"]  = "active"
    steps[3]["detail"] = "Applying pricing rules & peak multiplier..."
    render_steps(steps)
    time.sleep(0.3)

    # ── STEP 4: PRICING TOOL ────────────────────
    pricing = pricing_tool(distance, cab_type, trip["time"])

    # Also compute fares for all cab types (for comparison)
    all_fares = {ct: pricing_tool(distance, ct, trip["time"])["total_fare"] for ct in CAB_RATES}

    steps[3]["state"]  = "done"
    steps[3]["detail"] = f'Total: ₹{pricing["total_fare"]}'
    steps[4]["state"]  = "active"
    steps[4]["detail"] = "Building response..."
    render_steps(steps)
    time.sleep(0.25)

    steps[4]["state"]  = "done"
    steps[4]["detail"] = "Done ✓"
    render_steps(steps)
    time.sleep(0.2)

    # ── STEP 5: RENDER RESULT ───────────────────
    peak_label  = "⚡ Yes (×1.2 applied)" if pricing["peak_hour"] else "No"
    badge_class = {"Mini": "badge-mini", "Sedan": "badge-sedan", "SUV": "badge-suv"}[cab_type]
    cab_emoji   = {"Mini": "🚗", "Sedan": "🚙", "SUV": "🚐"}[cab_type]

    # Format date nicely
    try:
        date_nice = datetime.strptime(trip["date"], "%Y-%m-%d").strftime("%a, %d %b %Y")
    except Exception:
        date_nice = trip["date"]

    result_html = f"""
    <div class="result-card">
        <h3>🗺️ Trip Details</h3>
        <div class="result-row">
            <span class="result-label">📍 Pickup</span>
            <span class="result-value">{trip['pickup']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">🏁 Drop</span>
            <span class="result-value">{trip['drop']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">📅 Date</span>
            <span class="result-value">{date_nice}</span>
        </div>
        <div class="result-row">
            <span class="result-label">🕐 Time</span>
            <span class="result-value">{trip['time']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">📏 Distance</span>
            <span class="result-value">{distance} km</span>
        </div>
        <div class="result-row">
            <span class="result-label">⚡ Peak Hours</span>
            <span class="result-value">{peak_label}</span>
        </div>
        <div class="result-row">
            <span class="result-label">🏆 Recommended</span>
            <span class="result-value">
                <span class="cab-badge {badge_class}">{cab_emoji} {cab_type}</span>
            </span>
        </div>
    </div>

    <div class="fare-highlight">
        <div class="fare-amount">₹{pricing['total_fare']}</div>
        <div class="fare-label">Estimated fare · {cab_type} · {distance} km</div>
    </div>

    <div class="result-card" style="margin-top:1rem;">
        <h3>💰 Fare Breakdown</h3>
        <div class="result-row">
            <span class="result-label">Base Fare</span>
            <span class="result-value">₹{pricing['base_fare']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">Distance Charge ({distance} km × ₹{CAB_RATES[cab_type]}/km)</span>
            <span class="result-value">₹{pricing['distance_charge']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">Peak Multiplier</span>
            <span class="result-value">{pricing['multiplier']}×</span>
        </div>
        <div class="result-row" style="border-top: 1px solid #333; padding-top:10px; margin-top:6px;">
            <span class="result-label" style="font-weight:700; color:#e8eaf0;">Total</span>
            <span class="result-value" style="color:#f5c842; font-size:1.1rem;">₹{pricing['total_fare']}</span>
        </div>
    </div>

    <div class="result-card" style="margin-top:1rem;">
        <h3>🚘 All Cab Options</h3>
        <div class="result-row">
            <span class="result-label"><span class="cab-badge badge-mini">🚗 Mini</span></span>
            <span class="result-value">₹{all_fares['Mini']}</span>
        </div>
        <div class="result-row">
            <span class="result-label"><span class="cab-badge badge-sedan">🚙 Sedan</span></span>
            <span class="result-value">₹{all_fares['Sedan']}</span>
        </div>
        <div class="result-row">
            <span class="result-label"><span class="cab-badge badge-suv">🚐 SUV</span></span>
            <span class="result-value">₹{all_fares['SUV']}</span>
        </div>
    </div>
    """

    result_placeholder.markdown(result_html, unsafe_allow_html=True)

    # Return for chat history
    return {
        "trip":    trip,
        "distance": distance,
        "pricing":  pricing,
        "cab_type": cab_type,
        "all_fares": all_fares,
    }


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# ─────────────────────────────────────────────
# SAMPLE PROMPTS
# ─────────────────────────────────────────────
st.markdown("**💡 Try a sample booking:**")
col1, col2, col3 = st.columns(3)
samples = [
    "Book a cab from Meerut to Delhi tomorrow at 9 AM",
    "I need a ride from Noida to Gurgaon at 6 PM today",
    "Get me a cab from Delhi to Agra on 2025-08-10 at 7 AM",
]
for col, sample in zip([col1, col2, col3], samples):
    with col:
        if st.button(sample[:40] + "…", use_container_width=True):
            st.session_state.pending_prompt = sample

# ─────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### 💬 Conversation")
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-msg">🚕 {msg["content"]}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INPUT + SUBMIT
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🚀 Book Your Ride")

user_input = st.chat_input("e.g. Book a cab from Meerut to Delhi tomorrow at 9 AM")

# Use pending prompt from sample button, or typed input
query = st.session_state.pending_prompt or user_input
if st.session_state.pending_prompt:
    st.session_state.pending_prompt = None   # consume it

if query:
    if not GEMINI_API_KEY:
        st.markdown(
            '<div class="warn-box">⚠️ Please enter your Gemini API Key in the sidebar (or set the '
            '<code>GEMINI_API_KEY</code> environment variable).</div>',
            unsafe_allow_html=True
        )
    else:
        # Show user message
        st.markdown(f'<div class="user-msg">🧑 {query}</div>', unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "user", "content": query})

        st.markdown("#### 🤖 Agent Pipeline Running…")
        result = run_agentic_pipeline(query, GEMINI_API_KEY)

        if result:
            summary = (
                f"Trip: {result['trip']['pickup']} → {result['trip']['drop']} | "
                f"{result['distance']} km | ₹{result['pricing']['total_fare']} ({result['cab_type']})"
            )
            st.session_state.chat_history.append({"role": "assistant", "content": summary})

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#444; font-size:0.78rem;'>"
    "CabGPT · Agentic AI Demo · Built with Streamlit &amp; Gemini"
    "</p>",
    unsafe_allow_html=True,
)
