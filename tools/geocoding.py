from geopy.geocoders import Nominatim

def get_coordinates(location: str) -> dict:
    """
    Geocodes a location name to latitude, longitude, and formatted address using geopy (Nominatim).
    Returns: dict with {"lat", "lng", "formatted_address"} or {"error"}
    """
    try:
        geolocator = Nominatim(user_agent="cabgpt_agent")
        loc = geolocator.geocode(location, timeout=10)
        if loc:
            return {
                "lat": loc.latitude,
                "lng": loc.longitude,
                "formatted_address": loc.address
            }
        else:
            return {"error": f"Location '{location}' not found. Please try specifying the city or landmark name more clearly."}
    except Exception as e:
        return {"error": f"Geocoding failed: {str(e)}"}
