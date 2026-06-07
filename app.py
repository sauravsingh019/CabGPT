import streamlit as st
import json
import re
import time
import os
import random
import requests
from datetime import datetime

# Import agent and tools
from agent import run_agentic_loop, extract_intent_and_entities
from tools.geocoding import get_coordinates
from tools.fare_calculator import estimate_fare
import tools.maps
import tools.weather
from config import GEMINI_API_KEY, GOOGLE_MAPS_API_KEY, OPENWEATHER_API_KEY

# PAGE CONFIG
st.set_page_config(
    page_title="CabGPT – AI Booking Assistant",
    page_icon="🚕",
    layout="centered",
)

# HELPER UTILS
def clean_html(html_str: str) -> str:
    """Helper to strip leading spaces from HTML/SVG lines to prevent markdown code blocks."""
    if not html_str:
        return ""
    return "\n".join(line.strip() for line in html_str.splitlines())

# ─────────────────────────────────────────────
# CUSTOM CSS DEFINITIONS
# ─────────────────────────────────────────────
def get_custom_css() -> str:
    theme_vars = """
    --bg-color: #080a10;
    --sidebar-bg: #05060b;
    --text-color: #f1f3f9;
    --text-muted: #8a96ab;
    --card-bg: rgba(16, 20, 35, 0.7);
    --border-color: rgba(255, 255, 255, 0.08);
    --accent-primary: #ffb703;
    --accent-secondary: #fb8500;
    --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    --hover-shadow: 0 8px 32px 0 rgba(255, 183, 3, 0.18);
    
    --step-done-bg: rgba(76, 175, 80, 0.06);
    --step-done-border: #4caf50;
    --step-active-bg: rgba(255, 183, 3, 0.06);
    --step-active-border: #ffb703;
    --step-wait-bg: rgba(20, 24, 38, 0.4);
    --step-wait-border: rgba(255, 255, 255, 0.03);
    --step-wait-text: #4e5569;
    
    --bubble-user: rgba(251, 133, 0, 0.12);
    --bubble-user-border: rgba(251, 133, 0, 0.35);
    --bubble-bot: rgba(16, 20, 35, 0.85);
    --bubble-bot-border: rgba(255, 255, 255, 0.06);
    
    --input-bg: #0e111d;
    --input-border: rgba(255, 255, 255, 0.1);
    --input-focus: #ffb703;
    """
        
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {{
    {theme_vars}
}}

html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    transition: background-color 0.3s ease, color 0.3s ease;
}}

section[data-testid="stSidebar"] {{
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color) !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}}

.cab-header {{
    text-align: center;
    padding: 0.5rem 0 1.5rem;
}}
.cab-header h1 {{
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -2px;
    margin-bottom: 0.1rem;
}}
.cab-header p {{
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.2rem;
}}

.cab-card {{
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}}
.cab-card:hover {{
    border-color: var(--accent-primary);
}}

.agent-step {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 12px 18px;
    border-radius: 14px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    border: 1px solid var(--border-color);
    transition: all 0.3s ease;
}}
.step-done {{
    background: var(--step-done-bg);
    border-left: 4px solid var(--step-done-border);
}}
.step-active {{
    background: var(--step-active-bg);
    border-left: 4px solid var(--step-active-border);
    animation: step-pulse 2s infinite;
}}
.step-wait {{
    background: var(--step-wait-bg);
    border-left: 4px solid var(--step-wait-border);
    color: var(--step-wait-text);
}}
.step-icon {{
    font-size: 1.25rem;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    width: 24px;
}}
.step-label {{
    font-weight: 600;
    color: var(--text-color);
}}
.step-detail {{
    color: var(--text-muted);
    font-size: 0.78rem;
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}}

.nlp-extracted-panel {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
}}
.extracted-tag {{
    background: var(--border-color);
    border: 1px solid var(--border-color);
    color: var(--text-color);
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
}}

.user-msg {{
    background: var(--bubble-user);
    border: 1px solid var(--bubble-user-border);
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin-bottom: 12px;
    font-size: 0.92rem;
    color: var(--text-color);
    max-width: 85%;
    margin-left: auto;
    box-shadow: 0 4px 15px rgba(0,0,0,0.02);
}}
.bot-msg {{
    background: var(--bubble-bot);
    border: 1px solid var(--bubble-bot-border);
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin-bottom: 12px;
    font-size: 0.92rem;
    color: var(--text-color);
    max-width: 85%;
    box-shadow: var(--shadow);
}}

.option-select-card {{
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}}
.option-selected {{
    border-color: var(--accent-primary) !important;
    background: rgba(255, 183, 3, 0.06) !important;
}}

.result-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 11px 0;
    border-bottom: 1px solid var(--border-color);
    font-size: 0.9rem;
}}
.result-row:last-child {{
    border-bottom: none;
}}
.result-label {{
    color: var(--text-muted);
}}
.result-value {{
    color: var(--text-color);
    font-weight: 600;
}}

.warn-box {{
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 14px 18px;
    color: #fca5a5;
    font-size: 0.88rem;
    margin: 1rem 0;
}}

.info-banner {{
    background: rgba(251, 133, 0, 0.08);
    border: 1px solid rgba(251, 133, 0, 0.3);
    border-radius: 12px;
    padding: 14px 18px;
    color: #fbd38d;
    font-size: 0.88rem;
    margin: 1rem 0;
}}

@keyframes step-pulse {{
    0% {{ border-left-color: var(--accent-primary); }}
    50% {{ border-left-color: var(--accent-secondary); }}
    100% {{ border-left-color: var(--accent-primary); }}
}}
</style>
"""

# Render current CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="cab-header">
    <h1>🚕 CabGPT</h1>
    <p>Agentic AI · NLP Cab Booking &amp; Fare Estimation Assistant</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RESOLVE API KEY  (env var or sidebar input)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Credentials")
    if not GEMINI_API_KEY:
        gemini_input = st.text_input("Gemini API Key", type="password", help="Required for NLP processing & Agent tools")
        resolved_gemini_key = gemini_input.strip()
    else:
        st.success("✓ Gemini API Key loaded")
        resolved_gemini_key = GEMINI_API_KEY
        
    maps_input = st.text_input("Google Maps API Key (Optional)", type="password", value=GOOGLE_MAPS_API_KEY, help="Falls back to Geopy geodesic if empty")
    tools.maps.GOOGLE_MAPS_API_KEY = maps_input.strip()
    
    weather_input = st.text_input("OpenWeatherMap API Key (Optional)", type="password", value=OPENWEATHER_API_KEY, help="Falls back to clear weather if empty")
    tools.weather.OPENWEATHER_API_KEY = weather_input.strip()

    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline Stages")
    st.markdown("""
1. **NLP Extractor** – parses pickup & dropoff
2. **Geocode Tool** – resolves coordinates
3. **Route Agent** – measures road distance
4. **OWM Weather** – checks rainfall
5. **Surge Calculator** – dynamic modifiers
6. **Response Engine** – formats visual dashboards
    """)
    st.markdown("---")
    st.markdown("### 📍 Supported Cities")
    st.markdown("Meerut · Delhi · Noida · Gurgaon · Faridabad · Ghaziabad · Agra · Jaipur · Lucknow · Chandigarh · Bangalore · Mumbai")

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("recent_searches", [])
st.session_state.setdefault("pending_prompt", None)
st.session_state.setdefault("partial_trip", {"pickup": None, "drop": None, "date": None, "time": None})
st.session_state.setdefault("current_trip_data", None)
st.session_state.setdefault("selected_cab", None)
st.session_state.setdefault("booking_confirmed", False)
st.session_state.setdefault("driver_matched", False)
st.session_state.setdefault("pickup_coords", None)
st.session_state.setdefault("drop_coords", None)
st.session_state.setdefault("driver_chat_history", [])

# ─────────────────────────────────────────────
# ANIMATED SVG ROUTE MAP COMPONENT
# ─────────────────────────────────────────────
def render_svg_map(pickup: str, drop: str, p_coords=None, d_coords=None) -> str:
    COORDS = {
        "chandigarh": (180, 50, "Chandigarh"),
        "meerut": (320, 130, "Meerut"),
        "ghaziabad": (290, 170, "Ghaziabad"),
        "delhi": (250, 200, "Delhi"),
        "gurgaon": (205, 230, "Gurgaon"),
        "noida": (285, 220, "Noida"),
        "faridabad": (260, 250, "Faridabad"),
        "agra": (350, 315, "Agra"),
        "jaipur": (110, 290, "Jaipur"),
        "lucknow": (450, 350, "Lucknow"),
        "bangalore": (230, 340, "Bangalore"),
        "mumbai": (140, 310, "Mumbai")
    }
    
    p_lower = pickup.lower().strip() if pickup else ""
    d_lower = drop.lower().strip() if drop else ""
    
    # Map dynamic coordinates
    if p_lower and p_lower not in COORDS:
        if p_coords:
            COORDS[p_lower] = (120, 250, pickup.title())
        else:
            COORDS[p_lower] = (120, 250, pickup.title())
            
    if d_lower and d_lower not in COORDS:
        if d_coords:
            COORDS[d_lower] = (380, 150, drop.title())
        else:
            COORDS[d_lower] = (380, 150, drop.title())
            
    bg_color = "rgba(10, 13, 26, 0.4)"
    border_color = "var(--border-color)"
    dot_color = "rgba(255, 255, 255, 0.15)"
    text_color = "var(--text-muted)"
    
    p_info = COORDS.get(p_lower)
    d_info = COORDS.get(d_lower)
    
    svg_content = f"""
    <div style="width: 100%; display: flex; justify-content: center; margin: 0.5rem 0;">
    <svg width="100%" height="280" viewBox="0 0 500 400" style="background: {bg_color}; border-radius: 14px; border: 1px solid {border_color}; overflow: hidden;">
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.015)" stroke-width="1"/>
        </pattern>
        <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="var(--accent-primary)" />
          <stop offset="100%" stop-color="var(--accent-secondary)" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
    """
    
    for city_key, (x, y, name) in COORDS.items():
        is_active = (city_key == p_lower or city_key == d_lower)
        if not is_active:
            svg_content += f"""
            <circle cx="{x}" cy="{y}" r="4" fill="{dot_color}" />
            <text x="{x}" y="{y-8}" font-family="'Plus Jakarta Sans', sans-serif" font-size="10" fill="{text_color}" text-anchor="middle" opacity="0.5">{name}</text>
            """
            
    if p_info and d_info and p_lower != d_lower:
        px, py, pname = p_info
        dx, dy, dname = d_info
        mx = (px + dx) / 2
        my = (py + dy) / 2 - 40
        path_d = f"M {px} {py} Q {mx} {my} {dx} {dy}"
        
        svg_content += f"""
        <path d="{path_d}" fill="none" stroke="url(#routeGrad)" stroke-width="3" stroke-linecap="round" stroke-dasharray="6, 4" style="animation: route-dash 1.5s linear infinite;" />
        <g>
          <text font-size="20" x="-10" y="7">🚕</text>
          <animateMotion dur="4s" repeatCount="indefinite" path="{path_d}" rotate="auto" />
        </g>
        """
        
    for city_key, (x, y, name) in COORDS.items():
        is_pickup = (city_key == p_lower)
        is_drop = (city_key == d_lower)
        if is_pickup or is_drop:
            role_emoji = "📍" if is_pickup else "🏁"
            role_color = "var(--accent-primary)" if is_pickup else "var(--accent-secondary)"
            
            svg_content += f"""
            <circle cx="{x}" cy="{y}" r="8" fill="none" stroke="{role_color}" stroke-width="1.5" opacity="0.8">
              <animate attributeName="r" values="3;12;3" dur="2.5s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0;0.8" dur="2.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="{x}" cy="{y}" r="4.5" fill="{role_color}" />
            <g transform="translate({x}, {y-26})">
              <rect x="-35" y="-10" width="70" height="18" rx="4" fill="#111424" stroke="{role_color}" stroke-width="1" style="filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.1));" />
              <text x="0" y="2" font-family="'Plus Jakarta Sans', sans-serif" font-weight="bold" font-size="9" fill="var(--text-color)" text-anchor="middle">{role_emoji} {name}</text>
            </g>
            """
            
    svg_content += """
    </svg>
    </div>
    <style>
      @keyframes route-dash {
        to { stroke-dashoffset: -20; }
      }
    </style>
    """
    return clean_html(svg_content)

# ─────────────────────────────────────────────
# SIMULATED CHAT / BIDS GENERATOR
# ─────────────────────────────────────────────
def get_driver_response(user_msg: str, api_key: str, pickup: str, drop: str) -> str:
    if not api_key:
        return random.choice([
            "Haan bhaiya, main location ke paas hi hu, 2 minute mein aa raha hu.",
            "Ok bhaiya, main location par pahunch gaya hu, aap aa jaiye.",
            "Aap building ke paas khade ho kya? Main udhar hi aa raha hu."
        ])
    try:
        from google.generativeai import GenerativeModel
        model = GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        You are Rahul Kumar, a professional cab driver matched with a passenger.
        You drive a Silver Swift Dzire (UP-16-AB-8392).
        The passenger is traveling from {pickup} to {drop}.
        Respond to the passenger's message: "{user_msg}"
        Guidelines:
        - Persona: Natural, polite Indian cab driver.
        - Language: Hinglish (Hindi + English mix), standard for Indian cab drivers.
        - Output format: Under 2 sentences, brief, and friendly (e.g. use "Bhaiya" or "Sir").
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Haan sir, main aa raha hu, bas 2 minute."

def render_negotiation_console(logs: list[str]) -> str:
    log_lines = "".join(f"<div style='margin-bottom:3px;'>&gt; {l}</div>" for l in logs)
    html = f"""
    <div class="cab-card" style="background:#05060b; border: 1px solid var(--accent-primary); font-family:'JetBrains Mono', monospace; padding:12px 16px; border-radius:14px; margin-top:10px;">
        <div style="color:var(--accent-primary); font-weight:700; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:6px; font-size:0.85rem;">
           📟 Multi-Agent Negotiation Console
        </div>
        <div style="font-size:0.75rem; line-height:1.5; color:#a3b2cc; max-height:150px; overflow-y:auto; font-family:'JetBrains Mono', monospace;">
           {log_lines}
        </div>
    </div>
    """
    return clean_html(html)

# ─────────────────────────────────────────────
# DYNAMIC COORDINATE RESOLVER
# ─────────────────────────────────────────────
def resolve_coordinates(pickup, dropoff, tool_logs):
    p_coords, d_coords = None, None
    for log in tool_logs:
        if log["tool"] == "get_coordinates":
            loc_arg = log["args"].get("location", "").lower()
            res = log["result"]
            if "error" not in res:
                if pickup and pickup.lower() in loc_arg:
                    p_coords = (res["lat"], res["lng"], res["formatted_address"])
                elif dropoff and dropoff.lower() in loc_arg:
                    d_coords = (res["lat"], res["lng"], res["formatted_address"])
                    
    if not p_coords and pickup:
        try:
            res = get_coordinates(pickup)
            if "error" not in res:
                p_coords = (res["lat"], res["lng"], res["formatted_address"])
        except Exception:
            pass
    if not d_coords and dropoff:
        try:
            res = get_coordinates(dropoff)
            if "error" not in res:
                d_coords = (res["lat"], res["lng"], res["formatted_address"])
        except Exception:
            pass
    return p_coords, d_coords

# ─────────────────────────────────────────────
# VIEW FLOW: CONFIRMED BOOKING & ACTIVE TRIP
# ─────────────────────────────────────────────
if st.session_state.booking_confirmed and st.session_state.current_trip_data:
    trip_data = st.session_state.current_trip_data
    trip = trip_data["trip"]
    distance = trip_data["distance"]
    selected_cab = st.session_state.selected_cab or "Uber Go"
    fares = trip_data["fare_data"]["fares"]
    selected_fare = fares.get(selected_cab, {"min": 150, "max": 180, "eta": 4, "surge_applied": "None"})
    
    # Simulating driver matching sequence
    if not st.session_state.driver_matched:
        matching_placeholder = st.empty()
        with matching_placeholder.container():
            st.markdown(f"""
            <div class="cab-card" style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; animation: step-pulse 1.5s infinite;">🔍</div>
                <h3 style="color: var(--accent-primary); margin-top:10px;">Contacting Nearby Drivers...</h3>
                <p style="color: var(--text-muted); font-size: 0.88rem;">Broadcasting booking request for <b>{selected_cab}</b>...</p>
                <div style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:#888; margin-top:8px;">{trip['pickup']} ➔ {trip['drop']} ({distance} km)</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1.5)
            
            st.markdown(f"""
            <div class="cab-card" style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; animation: step-pulse 1.5s infinite;">🚕</div>
                <h3 style="color: var(--accent-secondary); margin-top:10px;">Driver Accepting Ride...</h3>
                <p style="color: var(--text-muted); font-size: 0.88rem;">Driver <b>Rahul Kumar</b> (4.9 ⭐) is accepting your request...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1.0)
        matching_placeholder.empty()
        st.session_state.driver_matched = True
        st.rerun()

    # RENDER CONFIRMED CARD
    map_html = render_svg_map(trip["pickup"], trip["drop"], st.session_state.pickup_coords, st.session_state.drop_coords)
    st.markdown(clean_html(f"""
    <div class="cab-card" style="border: 2px solid #4caf50; background: rgba(76, 175, 80, 0.04);">
        <h2 style="margin-top:0; color:#4caf50; font-size:1.35rem; display:flex; align-items:center; gap:8px;">
           🎉 Ride Booked Successfully!
        </h2>
        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:4px;">
           Rahul is arriving in {selected_fare['eta']} mins. Please meet at the designated pickup location.
        </p>
        
        <div style="display:flex; align-items:center; gap:16px; margin: 1rem 0; padding:12px; background:rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius:12px;">
            <div style="font-size:2.5rem; background:rgba(255,255,255,0.04); border-radius:50%; width:50px; height:50px; display:flex; align-items:center; justify-content:center;">👨🏽‍✈️</div>
            <div style="flex-grow:1;">
                <div style="font-size:1.1rem; font-weight:700; color:var(--text-color);">Rahul Kumar</div>
                <div style="font-size:0.8rem; color:#4caf50; font-weight:600;">⭐ 4.9 Rating · 2500+ Trips</div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Silver Maruti Swift Dzire</div>
            </div>
            <div style="text-align:right;">
                <div style="background:var(--accent-primary); color:#000; padding:4px 10px; border-radius:6px; font-weight:800; font-family:'JetBrains Mono', monospace; font-size:0.9rem;">UP-16-AB-8392</div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Ride OTP: <b style="color:var(--accent-primary); font-size:0.8rem;">4729</b></div>
            </div>
        </div>
        
        <div class="result-row">
            <span class="result-label">📍 Pickup Location</span>
            <span class="result-value" style="color: var(--accent-primary);">{trip['pickup']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">🏁 Destination</span>
            <span class="result-value" style="color: var(--accent-secondary);">{trip['drop']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">📏 Calculated Route Distance</span>
            <span class="result-value" style="font-family:'JetBrains Mono', monospace;">{distance} km</span>
        </div>
        <div class="result-row">
            <span class="result-label">🚘 Class Selected</span>
            <span class="result-value" style="font-family:'JetBrains Mono', monospace; font-weight:700; color:var(--accent-primary);">{selected_cab}</span>
        </div>
        <div class="result-row" style="border-top:1px dashed var(--border-color); padding-top:10px; margin-top:8px;">
            <span class="result-label" style="font-weight:700; color:var(--text-color);">Total Estimated Fare</span>
            <span class="result-value" style="color:var(--accent-primary); font-size:1.15rem; font-family:'JetBrains Mono', monospace;">₹{selected_fare['min']} - ₹{selected_fare['max']}</span>
        </div>
    </div>
    
    <div class="cab-card">
        <h3 style="margin-top:0; font-size:1rem; color:var(--accent-primary);">🗺️ Live Active Tracking</h3>
        {map_html}
    </div>
    """), unsafe_allow_html=True)
    
    # ── RAHUL CHAT CONSOLE ──
    st.markdown("---")
    st.markdown("<h3 style='color:var(--accent-primary); font-size:1.1rem;'>💬 Chat with Driver (Rahul)</h3>", unsafe_allow_html=True)
    
    chat_container_html = "<div style='background:rgba(16,20,35,0.7); border:1px solid var(--border-color); border-radius:12px; padding:12px; max-height:200px; overflow-y:auto; margin-bottom:12px;'>"
    if not st.session_state.driver_chat_history:
        chat_container_html += "<div style='color:var(--text-muted); font-size:0.8rem; text-align:center;'>No messages yet. Tell Rahul where you're waiting.</div>"
    else:
        for m in st.session_state.driver_chat_history:
            if m["role"] == "user":
                chat_container_html += f"""
                <div style="background:var(--bubble-user); border:1px solid var(--bubble-user-border); border-radius:10px 10px 2px 10px; padding:8px 12px; margin-bottom:6px; max-width:80%; margin-left:auto; font-size:0.8rem; text-align:right;">
                    <b>You:</b> {m['content']}
                </div>
                """
            else:
                chat_container_html += f"""
                <div style="background:var(--bubble-bot); border:1px solid var(--bubble-bot-border); border-radius:10px 10px 10px 2px; padding:8px 12px; margin-bottom:6px; max-width:80%; font-size:0.8rem;">
                    <b>Rahul:</b> {m['content']}
                </div>
                """
    chat_container_html += "</div>"
    st.markdown(clean_html(chat_container_html), unsafe_allow_html=True)
    
    with st.form(key="driver_msg_form", clear_on_submit=True):
        chat_col1, chat_col2 = st.columns([5, 1])
        with chat_col1:
            driver_msg_val = st.text_input("Send message to Rahul:", label_visibility="collapsed", placeholder="e.g., Bhaiya block A ke pass khada hu.")
        with chat_col2:
            msg_submit = st.form_submit_button("Send", use_container_width=True)
            
        if msg_submit and driver_msg_val.strip():
            st.session_state.driver_chat_history.append({"role": "user", "content": driver_msg_val})
            reply_text = get_driver_response(driver_msg_val, resolved_gemini_key, trip["pickup"], trip["drop"])
            st.session_state.driver_chat_history.append({"role": "driver", "content": reply_text})
            st.rerun()
            
    if st.button("❌ Cancel Booking & Request New Cab", use_container_width=True):
        st.session_state.booking_confirmed = False
        st.session_state.driver_matched = False
        st.session_state.selected_cab = None
        st.session_state.driver_chat_history = []
        st.rerun()

# ─────────────────────────────────────────────
# VIEW FLOW: CAB CHOICES DASHBOARD
# ─────────────────────────────────────────────
elif st.session_state.current_trip_data is not None:
    trip_data = st.session_state.current_trip_data
    trip = trip_data["trip"]
    distance = trip_data["distance"]
    fares = trip_data["fare_data"]["fares"]
    cheapest = trip_data["fare_data"]["cheapest"]
    fastest = trip_data["fare_data"]["fastest"]
    weather_info = trip_data.get("weather", {"condition": "Sunny", "temp_celsius": 25.0, "is_raining": False})
    
    # SVG Routing Map
    map_html = render_svg_map(trip["pickup"], trip["drop"], st.session_state.pickup_coords, st.session_state.drop_coords)
    
    # 1. Routing card
    st.markdown(clean_html(f"""
    <div class="cab-card">
        <h3 style="margin-top:0; font-size:1.1rem; color:var(--accent-primary); display:flex; align-items:center; gap:8px;">
           🗺️ Travel Path Routing
        </h3>
        {map_html}
    </div>
    """), unsafe_allow_html=True)
    
    # 2. Weather & Traffic Surge Alert Card
    w_emoji = "🌧️" if weather_info["is_raining"] else "☀️"
    surge_multiplier = 1.0
    reasons = []
    
    # Peak hour surge check
    hour_val = int(trip["time"].split(":")[0]) if trip.get("time") else 12
    is_peak = (8 <= hour_val < 10) or (17 <= hour_val < 20)
    
    if is_peak and weather_info["is_raining"]:
        surge_multiplier = 1.5
        reasons.append("Peak Hour & Heavy Rain (1.5x)")
    elif is_peak:
        surge_multiplier = 1.3
        reasons.append("Office Peak Hours (1.3x)")
    elif weather_info["is_raining"]:
        surge_multiplier = 1.2
        reasons.append("Heavy Drizzle / Rain (1.2x)")
    else:
        reasons.append("Off-Peak normal rate (1.0x)")
        
    st.markdown(clean_html(f"""
    <div class="cab-card" style="border-left: 4px solid var(--accent-primary); background: rgba(255, 183, 3, 0.02);">
        <h3 style="margin-top:0; font-size:1.05rem; color:var(--accent-primary);">⚡ Dynamic AI Surge Monitor</h3>
        <div style="font-size:0.88rem; display:flex; gap:16px; margin-bottom:6px;">
            <span>Weather Condition: <b>{w_emoji} {weather_info['condition']} ({weather_info['temp_celsius']}°C)</b></span>
            <span>Hour analyzed: <b>{trip['time']}</b></span>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">
            Surge modifiers activated: <b>{", ".join(reasons)}</b>. Pricing multiplier index: <b>{surge_multiplier}x</b>.
        </p>
    </div>
    """), unsafe_allow_html=True)
    
    # 3. Trip Parameters summary
    st.markdown(clean_html(f"""
    <div class="cab-card">
        <h3 style="margin-top:0; font-size:1.05rem; color:var(--accent-primary);">📋 Booking Trip Details</h3>
        <div class="result-row">
            <span class="result-label">📍 Pickup Location</span>
            <span class="result-value" style="color: var(--accent-primary);">{trip['pickup']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">🏁 Destination</span>
            <span class="result-value" style="color: var(--accent-secondary);">{trip['drop']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">📅 Date &amp; Time</span>
            <span class="result-value">{trip['date']} at {trip['time']}</span>
        </div>
        <div class="result-row">
            <span class="result-label">📏 Route Distance</span>
            <span class="result-value" style="font-family:'JetBrains Mono', monospace;">{distance} km</span>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # 4. Interactive Cab Class select list
    selected_cab = st.session_state.selected_cab or "Uber Go"
    
    st.markdown("<h3 style='font-size:1.05rem; color:var(--accent-primary); margin-left: 5px; margin-bottom:8px;'>🚘 Select Preferred Ride option:</h3>", unsafe_allow_html=True)
    
    for provider, val in fares.items():
        is_sel = (provider == selected_cab)
        sel_class = "option-selected" if is_sel else ""
        icon = "🏍️" if "Bike" in provider else "🛺" if "Auto" in provider else "🚗"
        
        st.markdown(clean_html(f"""
        <div class="option-select-card {sel_class}">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:1.4rem;">{icon}</span>
                <div>
                    <b>{provider}</b><br>
                    <span style="font-size:0.75rem; color:var(--text-muted);">ETA: {val['eta']} mins · {val['surge_applied']}</span>
                </div>
            </div>
            <div style="font-family:'JetBrains Mono', monospace; font-weight:800; font-size:1.05rem; color:var(--accent-primary);">
                ₹{val['min']} - ₹{val['max']}
            </div>
        </div>
        """), unsafe_allow_html=True)
        
    col1, col2 = st.columns([3, 2])
    with col1:
        cab_options = list(fares.keys())
        default_idx = cab_options.index(selected_cab) if selected_cab in cab_options else 0
        new_sel_cab = st.selectbox("Choose a category to book:", options=cab_options, index=default_idx, label_visibility="collapsed")
        st.session_state.selected_cab = new_sel_cab
    with col2:
        if st.button("🚕 Confirm & Book Cab", use_container_width=True):
            st.session_state.booking_confirmed = True
            st.rerun()
            
    # Projections Expanders & Clipboard Copies
    # Share summary code box
    st.markdown("---")
    st.markdown("<h3 style='font-size:1.05rem; color:var(--accent-primary);'>📋 Share Summary</h3>", unsafe_allow_html=True)
    summary_lines = [
        f"🚕 **CabGPT Cab Fare Estimation**",
        f"📍 Pickup: {trip['pickup']}",
        f"🏁 Dropoff: {trip['drop']}",
        f"📏 Route Distance: {distance} km",
        f"🌦 Weather: {weather_info['condition']} (Surge applied: {reasons[0]})",
        f"",
        f"💰 **Fares Comparison:**",
    ]
    for provider, val in fares.items():
        summary_lines.append(f"- {provider}: ₹{val['min']} - ₹{val['max']} (ETA: {val['eta']}m)")
        
    summary_text = "\n".join(summary_lines)
    st.code(summary_text, language="markdown")
    
    # Projections
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("🕐 **Travel Projections (+1hr, +2hr)**")
    p_now = fares[cheapest]["min"]
    p_plus1 = estimate_fare(distance, distance*2, weather_info["is_raining"], (hour_val+1)%24)["fares"][cheapest]["min"]
    p_plus2 = estimate_fare(distance, distance*2, weather_info["is_raining"], (hour_val+2)%24)["fares"][cheapest]["min"]
    
    col_n, col_p1, col_p2 = st.columns(3)
    col_n.metric(f"Now ({(hour_val)%24:02d}:00)", f"₹{p_now}", "Base rate")
    col_p1.metric(f"In 1 hr ({(hour_val+1)%24:02d}:00)", f"₹{p_plus1}", f"₹{p_plus1 - p_now:+d}", delta_color="inverse")
    col_p2.metric(f"In 2 hrs ({(hour_val+2)%24:02d}:00)", f"₹{p_plus2}", f"₹{p_plus2 - p_now:+d}", delta_color="inverse")
    st.markdown('</div>', unsafe_allow_html=True)

    # Developer Trace Console
    with st.expander("🛠️ Developer LLM Tool Trace Console", expanded=False):
        st.json(trip_data.get("tool_logs", []))

    if st.button("🔄 Request Another Fare Estimate", use_container_width=True):
        st.session_state.current_trip_data = None
        st.session_state.selected_cab = None
        st.rerun()

# ─────────────────────────────────────────────
# VIEW FLOW: CHAT & CLARIFICATION LOOP
# ─────────────────────────────────────────────
else:
    # ── Voice Speech-to-Text Button ──
    voice_html = """
    <div class="voice-booking-container" style="margin-bottom: 12px; text-align: left;">
        <button id="voice-mic-btn" style="
            background: linear-gradient(135deg, rgba(255, 183, 3, 0.1) 0%, rgba(251, 133, 0, 0.1) 100%);
            border: 1px solid var(--accent-primary);
            border-radius: 14px;
            color: var(--accent-primary);
            padding: 8px 16px;
            font-weight: 700;
            font-size: 0.85rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        " onclick="startVoiceRecognition(event)">
            🎙️ Speak Booking Request
        </button>
        <span id="voice-mic-status" style="font-size: 0.78rem; color: var(--text-muted); margin-left: 10px;"></span>
    </div>

    <script>
    function startVoiceRecognition(e) {
        e.preventDefault();
        const btn = document.getElementById('voice-mic-btn');
        const status = document.getElementById('voice-mic-status');
        
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            status.innerText = "Browser does not support Speech recognition. Use Chrome or Edge.";
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-IN';
        recognition.interimResults = false;
        
        recognition.onstart = function() {
            btn.innerHTML = '🔴 Listening...';
            btn.style.background = 'rgba(239, 68, 68, 0.1)';
            btn.style.borderColor = '#ef4444';
            btn.style.color = '#ef4444';
            status.innerText = "Speak now...";
        };
        
        recognition.onerror = function(event) {
            btn.innerHTML = '🎙️ Speak Booking Request';
            btn.style.background = 'rgba(255, 183, 3, 0.1)';
            btn.style.borderColor = 'var(--accent-primary)';
            btn.style.color = 'var(--accent-primary)';
            status.innerText = "Error: " + event.error;
        };
        
        recognition.onend = function() {
            btn.innerHTML = '🎙️ Speak Booking Request';
            btn.style.background = 'rgba(255, 183, 3, 0.1)';
            btn.style.borderColor = 'var(--accent-primary)';
            btn.style.color = 'var(--accent-primary)';
        };
        
        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            status.innerText = 'Transcribed: "' + text + '"';
            
            let ta = document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (!ta && typeof parent !== 'undefined') {
                ta = parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            }
            if (!ta && typeof window !== 'undefined' && window.parent) {
                ta = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            }
            
            if (ta) {
                ta.value = text;
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                ta.focus();
            } else {
                navigator.clipboard.writeText(text);
                status.innerText = 'Transcribed & Copied. Paste in Chat Input.';
            }
        };
        recognition.start();
    }
    </script>
    """
    st.markdown(clean_html(voice_html), unsafe_allow_html=True)

    # Chat message log display
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg"><b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-msg"><b>CabGPT:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    # Receive inputs
    user_input = st.chat_input("Compare Ola and Uber from Delhi Airport to Connaught Place...")
    query = st.session_state.pending_prompt or user_input
    
    if query:
        st.session_state.pending_prompt = None
        if not resolved_gemini_key:
            st.error("⚠️ Gemini API Key is missing. Please provide it in the sidebar configuration.")
        else:
            # Display user query
            st.markdown(f'<div class="user-msg"><b>You:</b><br>{query}</div>', unsafe_allow_html=True)
            st.session_state.chat_history.append({"role": "user", "content": query})
            
            # Show NLP Extraction Loader
            nlp_loader = st.empty()
            nlp_loader.markdown("""
            <div class="agent-step step-active">
                <span class="step-icon">🧠</span>
                <div>
                    <div class="step-label">NLP Agent Parsing Request</div>
                    <div class="step-detail">Extracting trip entities via Gemini LLM...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                extracted = extract_intent_and_entities(query, resolved_gemini_key)
                nlp_loader.empty()
                
                # Merge entities
                for k in ["pickup", "drop", "date", "time"]:
                    extracted_key = "dropoff" if k == "drop" else k
                    val = extracted.get(extracted_key) if k == "drop" else extracted.get(k)
                    if val:
                        st.session_state.partial_trip[k] = val
                        
            except Exception as e:
                nlp_loader.empty()
                st.error(f"❌ Intent Extraction failed: {str(e)}")
                st.stop()
                
            p = st.session_state.partial_trip
            
            # Check missing parameters
            missing = []
            if not p["pickup"]: missing.append("pickup location")
            if not p["drop"]: missing.append("drop location")
            if not p["date"]: missing.append("travel date")
            if not p["time"]: missing.append("travel time")
            
            # Prompt for missing elements or trigger agent
            if missing:
                if len(missing) == 3:
                    found = [k for k in ["pickup", "drop", "date", "time"] if p[k]][0]
                    reply = f"I've registered **{p[found]}**. Could you please specify **{', '.join(missing)}**?"
                elif len(missing) == 2:
                    reply = f"I have registered pickup: **{p['pickup'] or 'Not specified'}** and drop: **{p['drop'] or 'Not specified'}**. Please specify **{' and '.join(missing)}**."
                elif len(missing) == 1:
                    field = missing[0]
                    if field == "pickup location":
                        reply = f"I see you want to travel to **{p['drop']}** on **{p['date']}** at **{p['time']}**. What is your **pickup location**?"
                    elif field == "drop location":
                        reply = f"I've set your pickup from **{p['pickup']}** on **{p['date']}** at **{p['time']}**. What is your **drop location**?"
                    elif field == "travel date":
                        reply = f"I've registered a ride from **{p['pickup']}** to **{p['drop']}** at **{p['time']}**. What **date** should I schedule it for?"
                    else:
                        reply = f"I've registered a ride from **{p['pickup']}** to **{p['drop']}** on **{p['date']}**. What **time** should the driver arrive?"
                else:
                    reply = "I couldn't identify the travel route parameters. Please specify pickup city, destination, travel date, and time."
                    
                st.markdown(f'<div class="bot-msg"><b>CabGPT:</b><br>{reply}</div>', unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()
                
            else:
                # We have all parameters! Run the agent loop!
                resolved_trip = p.copy()
                st.session_state.partial_trip = {"pickup": None, "drop": None, "date": None, "time": None}
                
                # Show steps progress live
                steps_placeholder = st.empty()
                console_placeholder = st.empty()
                console_logs = []
                
                def render_steps(current_active: int, detail=""):
                    steps_list = [
                        {"icon": "🧠", "label": "NLP Intent Entity Extraction"},
                        {"icon": "📍", "label": "Geocoding coordinates resolver"},
                        {"icon": "📏", "label": "Distance Matrix Routing"},
                        {"icon": "🌦", "label": "OWM Live Weather Check"},
                        {"icon": "💰", "label": "Surge dynamic price calculator"},
                        {"icon": "✅", "label": "Response engine formatting"}
                    ]
                    html = ""
                    for idx, step in enumerate(steps_list):
                        if idx < current_active:
                            state_class = "step-done"
                        elif idx == current_active:
                            state_class = "step-active"
                        else:
                            state_class = "step-wait"
                        
                        det_str = f"<div class='step-detail'>{detail}</div>" if idx == current_active and detail else ""
                        html += f"""
                        <div class="agent-step {state_class}">
                            <span class="step-icon">{step['icon']}</span>
                            <div style="flex-grow:1;">
                                <div class="step-label">{step['label']}</div>
                                {det_str}
                            </div>
                        </div>
                        """
                    steps_placeholder.markdown(clean_html(html), unsafe_allow_html=True)
                    console_placeholder.markdown(render_negotiation_console(console_logs), unsafe_allow_html=True)
                
                # Turn loop callback
                def turn_callback(status_text):
                    console_logs.append(status_text.replace("**", ""))
                    # Map message content to steps
                    active_step = 1
                    if "distance" in status_text.lower():
                        active_step = 2
                    elif "weather" in status_text.lower():
                        active_step = 3
                    elif "fares" in status_text.lower() or "calculating" in status_text.lower():
                        active_step = 4
                    elif "surge" in status_text.lower():
                        active_step = 4
                    render_steps(active_step, status_text)
                    time.sleep(0.6)
                
                # Start
                console_logs.append("Initializing agentic cab booking loop...")
                console_logs.append(f"Query: '{query}'")
                render_steps(1, "📍 Resolving coordinates...")
                
                try:
                    # Run the agentic loop
                    response_text, tool_logs = run_agentic_loop(query, resolved_gemini_key, status_callback=turn_callback)
                    
                    render_steps(5, "Compiling visual results dashboard...")
                    time.sleep(0.5)
                    
                    steps_placeholder.empty()
                    console_placeholder.empty()
                    
                    # Parse results
                    fare_data = None
                    for log in reversed(tool_logs):
                        if log["tool"] == "estimate_fare" and "error" not in log["result"]:
                            fare_data = log["result"]
                            break
                            
                    p_coords, d_coords = None, None
                    weather_info = {"condition": "Sunny", "temp_celsius": 25.0, "is_raining": False}
                    distance = 10.0
                    
                    if fare_data:
                        p_coords, d_coords = resolve_coordinates(resolved_trip["pickup"], resolved_trip["drop"], tool_logs)
                        st.session_state.pickup_coords = p_coords
                        st.session_state.drop_coords = d_coords
                        
                        # Extract distance and weather from tool logs
                        for log in tool_logs:
                            if log["tool"] == "get_distance_and_duration":
                                distance = log["result"].get("distance_km", 10.0)
                            elif log["tool"] == "get_weather":
                                weather_info = log["result"]
                                
                        # Save Recent Search
                        search_item = {"pickup": resolved_trip["pickup"], "dropoff": resolved_trip["drop"], "query": query}
                        if search_item not in st.session_state.recent_searches:
                            st.session_state.recent_searches.insert(0, search_item)
                            st.session_state.recent_searches = st.session_state.recent_searches[:5]
                            
                        st.session_state.current_trip_data = {
                            "trip": resolved_trip,
                            "distance": distance,
                            "fare_data": fare_data,
                            "weather": weather_info,
                            "tool_logs": tool_logs
                        }
                        st.session_state.selected_cab = list(fare_data["fares"].keys())[0]
                        st.rerun()
                    else:
                        # General query or no fares computed
                        st.markdown(f'<div class="bot-msg"><b>CabGPT:</b><br>{response_text}</div>', unsafe_allow_html=True)
                        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                        st.rerun()
                        
                except Exception as e:
                    steps_placeholder.empty()
                    console_placeholder.empty()
                    err_msg = str(e)
                    st.error(f"❌ Execution Error: {err_msg}")
                    st.stop()

    # Suggestions list
    if not st.session_state.chat_history:
        st.markdown("### 💡 Sample Prompts:")
        samples = [
            "Book a cab from Meerut to Delhi tomorrow at 9 AM",
            "I need a ride from Noida to Gurgaon at 6 PM today",
            "Compare Ola and Uber from Andheri to Bandra at 11 AM",
            "Is it worth taking Rapido in Bangalore rain?"
        ]
        col1, col2 = st.columns(2)
        for idx, sample in enumerate(samples):
            col = col1 if idx % 2 == 0 else col2
            if col.button(sample, key=f"sample_{idx}", use_container_width=True):
                st.session_state.pending_prompt = sample
                st.rerun()

# FOOTER
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#555; font-size:0.75rem;'>"
    "CabGPT · Agentic AI Assistant · Built with Streamlit &amp; Gemini"
    "</p>",
    unsafe_allow_html=True,
)
