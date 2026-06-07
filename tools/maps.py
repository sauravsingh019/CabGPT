import googlemaps
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from config import GOOGLE_MAPS_API_KEY
import logging

def get_distance_and_duration(origin: str, destination: str) -> dict:
    """
    Retrieves route distance (in km) and duration (in minutes) between origin and destination.
    Uses Google Maps Distance Matrix API, or falls back to geopy Nominatim + geodesic distance.
    Returns: dict with {"distance_km", "duration_minutes", "origin_address", "destination_address", "is_fallback"}
    """
    if GOOGLE_MAPS_API_KEY:
        try:
            gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
            result = gmaps.distance_matrix(origins=[origin], destinations=[destination], mode="driving")
            
            if result.get("status") == "OK":
                row = result["rows"][0]
                element = row["elements"][0]
                if element.get("status") == "OK":
                    distance_m = element["distance"]["value"]
                    duration_s = element["duration"]["value"]
                    
                    return {
                        "distance_km": round(distance_m / 1000.0, 2),
                        "duration_minutes": round(duration_s / 60.0, 1),
                        "origin_address": result["origin_addresses"][0],
                        "destination_address": result["destination_addresses"][0],
                        "is_fallback": False
                    }
                else:
                    logging.warning(f"Google Maps element status is {element.get('status')}")
            else:
                logging.warning(f"Google Maps response status is {result.get('status')}")
        except Exception as e:
            logging.error(f"Google Maps API call failed: {str(e)}")
            # Fall through to geopy fallback
            
    # Geopy fallback
    try:
        geolocator = Nominatim(user_agent="cabgpt_agent")
        loc_origin = geolocator.geocode(origin, timeout=10)
        loc_dest = geolocator.geocode(destination, timeout=10)
        
        if not loc_origin:
            return {"error": f"Could not geocode origin location: '{origin}'"}
        if not loc_dest:
            return {"error": f"Could not geocode destination location: '{destination}'"}
            
        coords_origin = (loc_origin.latitude, loc_origin.longitude)
        coords_dest = (loc_dest.latitude, loc_dest.longitude)
        
        # Calculate straight-line distance
        distance_km = geodesic(coords_origin, coords_dest).kilometers
        # In city routing, standard routing distance is usually ~1.3 times straight-line distance
        routing_distance_km = round(distance_km * 1.3, 2)
        
        # Estimate duration assuming 30 km/h average speed in city driving
        duration_minutes = round((routing_distance_km / 30.0) * 60.0, 1)
        
        return {
            "distance_km": routing_distance_km,
            "duration_minutes": duration_minutes,
            "origin_address": loc_origin.address,
            "destination_address": loc_dest.address,
            "is_fallback": True
        }
    except Exception as e:
        return {"error": f"Distance estimation failed (including geopy fallback): {str(e)}"}
