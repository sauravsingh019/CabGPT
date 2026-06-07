import requests
from config import OPENWEATHER_API_KEY
import logging

def get_weather(lat: float, lng: float) -> dict:
    """
    Fetches current weather for given coordinates using OpenWeatherMap API.
    Returns: dict with {"condition", "temp_celsius", "is_raining", "is_fallback"}
    """
    if OPENWEATHER_API_KEY:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                weather_main = data.get("weather", [{}])[0].get("main", "Clear")
                temp = data.get("main", {}).get("temp", 25.0)
                
                # Check if it is raining
                is_raining = weather_main.lower() in ["rain", "drizzle", "thunderstorm"]
                
                return {
                    "condition": weather_main,
                    "temp_celsius": temp,
                    "is_raining": is_raining,
                    "is_fallback": False
                }
            else:
                logging.warning(f"OpenWeatherMap returned code {response.status_code}")
        except Exception as e:
            logging.error(f"OpenWeatherMap API call failed: {str(e)}")
            
    # Fallback when key is missing or API fails
    return {
        "condition": "Weather Data Unavailable",
        "temp_celsius": 25.0,
        "is_raining": False,
        "is_fallback": True
    }
