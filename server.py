from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import random
import logging
import socket
import subprocess
import time
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Helper to check if Ollama is running on port 11434
def is_ollama_running():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect(("127.0.0.1", 11434))
            return True
    except Exception:
        return False

# Attempt to programmatically start Ollama in the background on Windows
def start_ollama():
    if is_ollama_running():
        logging.info("Ollama is already running and listening on port 11434.")
        return
        
    logging.info("Ollama is not running. Attempting to start background service...")
    
    # Locate Windows Local App Data installation path
    appdata = os.getenv("LOCALAPPDATA")
    ollama_path = "ollama"  # Default in System PATH
    if appdata:
        candidate_path = os.path.join(appdata, "Programs", "Ollama", "ollama.exe")
        if os.path.exists(candidate_path):
            ollama_path = candidate_path
            
    try:
        subprocess.Popen([ollama_path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Spawned 'ollama serve' subprocess.")
        
        # Verify if listening
        for i in range(6):
            if is_ollama_running():
                logging.info("Ollama has successfully started.")
                return
            time.sleep(1)
        logging.warning("Ollama process launched but is not yet responding on port 11434.")
    except Exception as e:
        logging.error(f"Failed to auto-start Ollama process: {str(e)}")

# Launch Ollama background server
start_ollama()

# Import agent and tools from local codebase
from agent import run_agentic_loop, extract_intent_and_entities
from tools.geocoding import get_coordinates
from tools.maps import get_distance_and_duration
from tools.weather import get_weather
from tools.fare_calculator import estimate_fare, get_peak_hour_info

# Helper to resolve coordinates from logs or direct fallback
def resolve_coordinates(pickup, dropoff, tool_logs):
    p_coords, d_coords = None, None
    for log in tool_logs:
        if log["tool"] == "get_coordinates":
            loc_arg = log["args"].get("location", "").lower()
            res = log["result"]
            if "error" not in res:
                if pickup and pickup.lower() in loc_arg:
                    p_coords = {"lat": res["lat"], "lng": res["lng"], "address": res["formatted_address"]}
                elif dropoff and dropoff.lower() in loc_arg:
                    d_coords = {"lat": res["lat"], "lng": res["lng"], "address": res["formatted_address"]}
                    
    if not p_coords and pickup:
        try:
            res = get_coordinates(pickup)
            if "error" not in res:
                p_coords = {"lat": res["lat"], "lng": res["lng"], "address": res["formatted_address"]}
        except Exception:
            pass
    if not d_coords and dropoff:
        try:
            res = get_coordinates(dropoff)
            if "error" not in res:
                d_coords = {"lat": res["lat"], "lng": res["lng"], "address": res["formatted_address"]}
        except Exception:
            pass
    return p_coords, d_coords

# Helper for driver response simulation via Ollama
def get_driver_response(user_msg: str, model_name: str, pickup: str, drop: str) -> str:
    try:
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
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Handle dict or object response structure
        if isinstance(response, dict):
            return response.get("message", {}).get("content", "").strip()
        else:
            msg = getattr(response, "message", None)
            return (getattr(msg, "content", "") or "").strip()
            
    except Exception as e:
        logging.error(f"Ollama driver chat simulation failed: {str(e)}")
        return "Haan sir, main aa raha hu, bas 2 minute."

# --- API Endpoints ---

@app.route('/')
def home():
    """Serves the main landing page."""
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def list_models():
    """Returns a list of locally pulled Ollama models."""
    try:
        models_response = ollama.list()
        models_list = []
        for item in models_response.get("models", []):
            model_name = None
            if isinstance(item, dict):
                model_name = item.get("model") or item.get("name")
            else:
                model_name = getattr(item, "model", None) or getattr(item, "name", None)
            if model_name:
                models_list.append(model_name)
            
        # Fallback list if no models are returned
        if not models_list:
            models_list = ["llama3.1", "mistral", "gemma2", "phi3"]
        return jsonify({"models": models_list})
    except Exception as e:
        logging.error(f"Failed to query Ollama model tags: {str(e)}")
        # Graceful return with default choices
        return jsonify({"models": ["llama3.1", "mistral", "gemma2", "phi3", "llama3.2"]})

@app.route('/api/quick_fare', methods=['POST'])
def quick_fare():
    """
    Fast fare estimation — NO LLM involved.
    Directly calls: geocode → distance → weather → fare.
    Accepts: { pickup, dropoff, time_preference, cab_pref, vehicle_pref, travel_hour }
    """
    try:
        import datetime
        data = request.json or {}
        pickup = data.get('pickup', '').strip()
        dropoff = data.get('dropoff', '').strip()
        time_preference = data.get('time_preference', 'Now')
        cab_pref = data.get('cab_pref', 'Any')
        vehicle_pref = data.get('vehicle_pref', 'Any')
        travel_hour = data.get('travel_hour', datetime.datetime.now().hour)

        if not pickup:
            return jsonify({"error": "Pickup location is required"}), 400
        if not dropoff:
            return jsonify({"error": "Destination location is required"}), 400

        tool_logs = []

        # Step 1: Geocode pickup
        p_res = get_coordinates(pickup)
        tool_logs.append({"tool": "get_coordinates", "args": {"location": pickup}, "result": p_res})
        if "error" in p_res:
            return jsonify({"error": f"Could not find: '{pickup}'. Try a city name like 'Meerut' or 'Delhi'."}), 400
        p_coords = {"lat": p_res["lat"], "lng": p_res["lng"], "address": p_res["formatted_address"]}

        # Step 2: Geocode destination
        d_res = get_coordinates(dropoff)
        tool_logs.append({"tool": "get_coordinates", "args": {"location": dropoff}, "result": d_res})
        if "error" in d_res:
            return jsonify({"error": f"Could not find: '{dropoff}'. Try a city name like 'Delhi' or 'Noida'."}), 400
        d_coords = {"lat": d_res["lat"], "lng": d_res["lng"], "address": d_res["formatted_address"]}

        # Step 3: Get road distance
        dist_res = get_distance_and_duration(pickup, dropoff)
        tool_logs.append({"tool": "get_distance_and_duration", "args": {"origin": pickup, "destination": dropoff}, "result": dist_res})
        if "error" in dist_res:
            from geopy.distance import geodesic
            straight_km = geodesic((p_res["lat"], p_res["lng"]), (d_res["lat"], d_res["lng"])).kilometers
            routing_km = round(straight_km * 1.3, 2)
            dist_res = {
                "distance_km": routing_km,
                "duration_minutes": round((routing_km / 30.0) * 60.0, 1),
                "is_fallback": True
            }

        distance_km = dist_res.get("distance_km", 10.0)
        duration_mins = dist_res.get("duration_minutes", dist_res.get("duration_mins", 30.0))

        # Step 4: Get weather at pickup
        weather_res = get_weather(p_res["lat"], p_res["lng"])
        tool_logs.append({"tool": "get_weather", "args": {"lat": p_res["lat"], "lng": p_res["lng"]}, "result": weather_res})

        # Step 5: Peak hour info
        peak_res = get_peak_hour_info(int(travel_hour))
        tool_logs.append({"tool": "get_peak_hour_info", "args": {"hour": travel_hour}, "result": peak_res})

        # Step 6: Estimate fares
        fare_res = estimate_fare(
            distance_km=distance_km,
            duration_minutes=duration_mins,
            is_raining=weather_res.get("is_raining", False),
            current_hour=int(travel_hour)
        )
        tool_logs.append({"tool": "estimate_fare", "args": {
            "distance_km": distance_km,
            "duration_minutes": duration_mins,
            "is_raining": weather_res.get("is_raining", False),
            "current_hour": int(travel_hour)
        }, "result": fare_res})

        trip_payload = {
            "trip": {
                "pickup": pickup,
                "drop": dropoff,
                "date": time_preference,
                "time": f"{int(travel_hour):02d}:00"
            },
            "distance": distance_km,
            "duration_mins": duration_mins,
            "fare_data": fare_res,
            "weather": weather_res,
            "pickup_coords": p_coords,
            "drop_coords": d_coords,
            "peak_info": peak_res,
            "filters": {"cab_pref": cab_pref, "vehicle_pref": vehicle_pref}
        }

        return jsonify({
            "type": "trip_options",
            "trip_data": trip_payload,
            "tool_logs": tool_logs,
            "response": f"Fare estimates ready for {pickup} → {dropoff} ({distance_km} km)"
        })

    except Exception as e:
        logging.error(f"Error handling /api/quick_fare: {str(e)}")
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Runs NLP extraction + agentic tool loop via Ollama.
    Falls back to direct tool execution if the model hallucinated instead of calling tools.
    """
    try:
        import datetime
        data = request.json or {}
        query = data.get('query', '').strip()
        model_name = data.get('model_name', 'llama3.1').strip()

        if not query:
            return jsonify({"error": "Query is required"}), 400

        if not is_ollama_running():
            return jsonify({"error": "Ollama service is not running on port 11434. Please start it."}), 500

        # ── Step 1: NLP extract intent + entities ─────────────
        intent_data = extract_intent_and_entities(query, model_name)
        pickup = intent_data.get("pickup")
        drop   = intent_data.get("dropoff")

        # ── Step 2: Run agentic loop (LLM may or may not call tools) ─
        response_text, tool_logs = run_agentic_loop(query, model_name)

        # ── Step 3: Check if the LLM actually ran estimate_fare ───────
        fare_data    = None
        distance_km  = None
        duration_min = None
        weather_info = None
        peak_info    = None

        for log in tool_logs:
            t = log["tool"]
            r = log["result"]
            if "error" in r:
                continue
            if t == "estimate_fare":
                fare_data = r
            elif t == "get_distance_and_duration":
                distance_km  = r.get("distance_km")
                duration_min = r.get("duration_minutes") or r.get("duration_mins")
            elif t == "get_weather":
                weather_info = r
            elif t == "get_peak_hour_info":
                peak_info = r

        # ── Step 4: FALLBACK — if LLM hallucinated, run tools ourselves ─
        # This handles models (Mistral, Phi, etc.) that describe tool calls
        # instead of actually invoking them.
        if pickup and drop and not fare_data:
            logging.info(f"LLM did not call tools. Running fallback for: {pickup} → {drop}")
            fallback_logs = []

            p_res = get_coordinates(pickup)
            fallback_logs.append({"tool": "get_coordinates", "args": {"location": pickup}, "result": p_res})

            d_res = get_coordinates(drop)
            fallback_logs.append({"tool": "get_coordinates", "args": {"location": drop}, "result": d_res})

            if "error" not in p_res and "error" not in d_res:
                dist_res = get_distance_and_duration(pickup, drop)
                fallback_logs.append({"tool": "get_distance_and_duration", "args": {"origin": pickup, "destination": drop}, "result": dist_res})

                if "error" in dist_res:
                    from geopy.distance import geodesic
                    straight = geodesic((p_res["lat"], p_res["lng"]), (d_res["lat"], d_res["lng"])).kilometers
                    dist_res = {
                        "distance_km": round(straight * 1.3, 2),
                        "duration_minutes": round(straight * 1.3 / 30 * 60, 1),
                        "is_fallback": True
                    }

                distance_km  = dist_res.get("distance_km", 10.0)
                duration_min = dist_res.get("duration_minutes", 30.0)

                weather_info = get_weather(p_res["lat"], p_res["lng"])
                fallback_logs.append({"tool": "get_weather", "args": {"lat": p_res["lat"], "lng": p_res["lng"]}, "result": weather_info})

                current_hour = datetime.datetime.now().hour
                peak_info = get_peak_hour_info(current_hour)
                fallback_logs.append({"tool": "get_peak_hour_info", "args": {"hour": current_hour}, "result": peak_info})

                fare_data = estimate_fare(
                    distance_km=distance_km,
                    duration_minutes=duration_min,
                    is_raining=weather_info.get("is_raining", False),
                    current_hour=current_hour
                )
                fallback_logs.append({"tool": "estimate_fare", "args": {
                    "distance_km": distance_km,
                    "duration_minutes": duration_min,
                    "is_raining": weather_info.get("is_raining", False),
                    "current_hour": current_hour
                }, "result": fare_data})

                # Merge fallback logs so frontend shows full trace
                tool_logs = fallback_logs + tool_logs

        # ── Step 5: Build response ─────────────────────────────
        if fare_data and pickup and drop:
            p_coords, d_coords = resolve_coordinates(pickup, drop, tool_logs)
            trip_payload = {
                "trip": {
                    "pickup": pickup,
                    "drop": drop,
                    "date": intent_data.get("time_preference") or "Today",
                    "time": f"{datetime.datetime.now().hour:02d}:00"
                },
                "distance":     distance_km or 10.0,
                "duration_mins": duration_min or 30.0,
                "fare_data":    fare_data,
                "weather":      weather_info or {"condition": "Clear", "temp_celsius": 25, "is_raining": False},
                "pickup_coords": p_coords,
                "drop_coords":   d_coords,
                "peak_info":    peak_info or {}
            }
            return jsonify({
                "type": "trip_options",
                "trip_data": trip_payload,
                "tool_logs": tool_logs,
                "response": response_text
            })
        else:
            return jsonify({
                "type": "general",
                "response": response_text,
                "tool_logs": tool_logs
            })

    except Exception as e:
        logging.error(f"Error handling /api/chat: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/api/driver_chat', methods=['POST'])
def driver_chat():
    """Simulates driver responses using Ollama."""
    try:
        data = request.json or {}
        user_message = data.get('user_message', '').strip()
        pickup = data.get('pickup', '').strip()
        drop = data.get('drop', '').strip()
        model_name = data.get('model_name', 'llama3.1').strip()
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
            
        reply = get_driver_response(user_message, model_name, pickup, drop)
        return jsonify({"reply": reply})
        
    except Exception as e:
        logging.error(f"Error handling /api/driver_chat: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    logging.info("Starting CabGPT web server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
