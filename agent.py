import ollama
import json
import logging
from prompts import SYSTEM_PROMPT

# Import tools
from tools import get_coordinates, get_distance_and_duration, get_weather, estimate_fare, get_peak_hour_info

OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "Get latitude, longitude, and formatted address for a location name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or place name, e.g. 'Meerut', 'Delhi'."
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_distance_and_duration",
            "description": "Get road distance (km) and driving duration (mins) between origin and destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Starting location city/place name"},
                    "destination": {"type": "string", "description": "End location city/place name"}
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather condition and temperature for a given latitude and longitude.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude coordinate"},
                    "lng": {"type": "number", "description": "Longitude coordinate"}
                },
                "required": ["lat", "lng"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_fare",
            "description": "Estimate taxi fare (min/max range) for Ola, Uber, and Rapido based on distance, duration, weather rain, and hour of travel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance_km": {"type": "number", "description": "Total route distance in km"},
                    "duration_minutes": {"type": "number", "description": "Total duration in minutes"},
                    "is_raining": {"type": "boolean", "description": "True if rain is active"},
                    "current_hour": {"type": "integer", "description": "Hour of travel (0-23)"}
                },
                "required": ["distance_km", "duration_minutes", "is_raining", "current_hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_peak_hour_info",
            "description": "Get peak hour surge multiplier and traveling recommendations for a given hour.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hour": {"type": "integer", "description": "Hour of travel (0-23)"}
                },
                "required": ["hour"]
            }
        }
    }
]


def _get_ollama_message_parts(response):
    """
    Safely extract (content, tool_calls) from an Ollama response,
    handling both dict-style and object-style SDK responses.
    """
    if isinstance(response, dict):
        message = response.get("message", {})
        if isinstance(message, dict):
            return message.get("content", "") or "", message.get("tool_calls", []) or [], message
        else:
            content = getattr(message, "content", "") or ""
            tool_calls = getattr(message, "tool_calls", None) or []
            return content, tool_calls, {"role": "assistant", "content": content}
    else:
        raw_msg = getattr(response, "message", None)
        if raw_msg is None:
            return "", [], {"role": "assistant", "content": ""}
        content = getattr(raw_msg, "content", "") or ""
        tool_calls = getattr(raw_msg, "tool_calls", None) or []
        return content, tool_calls, {"role": "assistant", "content": content}


def _normalize_tool_call(call):
    """Extract (fn_name, fn_args) from either dict or object tool call."""
    if isinstance(call, dict):
        fn = call.get("function", {})
        name = fn.get("name") if isinstance(fn, dict) else getattr(fn, "name", None)
        args = fn.get("arguments", {}) if isinstance(fn, dict) else (getattr(fn, "arguments", {}) or {})
    else:
        fn_obj = getattr(call, "function", None)
        name = getattr(fn_obj, "name", None) if fn_obj else None
        args = getattr(fn_obj, "arguments", {}) if fn_obj else {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
    return name, args or {}


def extract_intent_and_entities(query: str, model_name: str) -> dict:
    """
    NLP layer — extracts intent + entities from Hinglish/English queries.
    Intents: 'fare_estimate' | 'comparison' | 'best_option' | 'general_question'
    """
    if not model_name:
        model_name = "llama3.1"

    try:
        prompt = f"""You are a JSON extraction bot for an Indian cab booking app.
Extract pickup, drop, time, and cab preference from the query.

Hinglish patterns to understand:
- "X se Y jaana hai" → pickup=X, dropoff=Y
- "X to Y" / "X se Y" → pickup=X, dropoff=Y
- "kal subah 9 baje" → time_preference="tomorrow at 9 AM"
- "aaj raat" → time_preference="tonight"
- "abhi" → time_preference="now"

Query: "{query}"

Reply ONLY with valid JSON, nothing else:
{{
  "intent": "fare_estimate",
  "pickup": "<city name or null>",
  "dropoff": "<city name or null>",
  "time_preference": "<time or null>",
  "cab_type_preference": "<Ola|Uber|Rapido|auto|bike|null>"
}}"""

        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        content, _, _ = _get_ollama_message_parts(response)
        data = json.loads(content)
        return {
            "intent": data.get("intent", "general_question"),
            "pickup": data.get("pickup"),
            "dropoff": data.get("dropoff"),
            "time_preference": data.get("time_preference"),
            "cab_type_preference": data.get("cab_type_preference")
        }
    except Exception as e:
        logging.error(f"NLP intent extraction failed: {str(e)}")
        return {
            "intent": "general_question",
            "pickup": None,
            "dropoff": None,
            "time_preference": None,
            "cab_type_preference": None
        }


def run_agentic_loop(query: str, model_name: str, status_callback=None) -> tuple[str, list[dict]]:
    """
    Executes the agentic tool loop with the selected local Ollama model.
    Handles both dict-style and object-style Ollama SDK responses.
    Returns: (final_response_text, tool_execution_logs)
    """
    if not model_name:
        model_name = "llama3.1"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    tool_logs = []
    max_turns = 10

    fn_map = {
        "get_coordinates": get_coordinates,
        "get_distance_and_duration": get_distance_and_duration,
        "get_weather": get_weather,
        "estimate_fare": estimate_fare,
        "get_peak_hour_info": get_peak_hour_info
    }

    for turn in range(max_turns):
        try:
            response = ollama.chat(
                model=model_name,
                messages=messages,
                tools=OLLAMA_TOOLS
            )
        except Exception as e:
            logging.error(f"Ollama chat error on turn {turn}: {str(e)}")
            return (
                f"Oops! '{model_name}' model se connect nahi ho paya. "
                f"Kya Ollama chal raha hai? Error: {str(e)}",
                tool_logs
            )

        # Normalize response
        msg_content, msg_tool_calls, msg_dict = _get_ollama_message_parts(response)

        # Always append a clean dict to messages
        messages.append(msg_dict)

        # No tool calls → final text answer
        if not msg_tool_calls:
            return msg_content.strip(), tool_logs

        # Execute each tool call
        for call in msg_tool_calls:
            fn_name, fn_args = _normalize_tool_call(call)
            if not fn_name:
                continue

            # Status callback for UI
            if status_callback:
                labels = {
                    "get_coordinates": f"📍 Geocoding: {fn_args.get('location')}",
                    "get_distance_and_duration": f"📏 Route: {fn_args.get('origin')} → {fn_args.get('destination')}",
                    "get_weather": "🌦 Checking weather...",
                    "estimate_fare": "💰 Calculating fares...",
                    "get_peak_hour_info": f"⚡ Surge check for hour {fn_args.get('hour')}"
                }
                status_callback(labels.get(fn_name, fn_name))

            # Run the tool
            try:
                if fn_name in fn_map:
                    result = fn_map[fn_name](**fn_args)
                else:
                    result = {"error": f"Tool '{fn_name}' is not defined."}
            except Exception as e:
                result = {"error": f"Tool execution failed: {str(e)}"}

            tool_logs.append({"tool": fn_name, "args": fn_args, "result": result})

            messages.append({
                "role": "tool",
                "content": json.dumps(result),
                "name": fn_name
            })

    return "Kuch gadbad ho gayi — agent maximum turns pe pahunch gaya.", tool_logs
