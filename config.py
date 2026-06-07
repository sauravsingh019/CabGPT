from dotenv import load_dotenv
import os

load_dotenv()

def get_secret(key: str) -> str:
    """Tries .env first, then environment variables. Returns empty string for optional keys."""
    value = os.getenv(key, "")
    # Treat placeholder values as empty
    if value and ("your_" in value.lower() or "here" in value.lower()):
        value = ""
    return value

# Optional keys — graceful fallback if not set
GEMINI_API_KEY       = get_secret("GEMINI_API_KEY")      # Not needed for Ollama
GOOGLE_MAPS_API_KEY  = get_secret("GOOGLE_MAPS_API_KEY") # Optional — falls back to geopy
OPENWEATHER_API_KEY  = get_secret("OPENWEATHER_API_KEY") # Optional — falls back to clear weather
