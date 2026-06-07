def get_peak_hour_info(hour: int) -> dict:
    """
    Checks if a given hour is a peak hour and returns surge details.
    Peak hours are defined as 8-10 AM (8:00 - 9:59) and 5-8 PM (17:00 - 19:59).
    """
    is_peak = (8 <= hour < 10) or (17 <= hour < 20)
    if is_peak:
        if 8 <= hour < 10:
            peak_label = "Morning Peak Hours"
            recommendation = "High demand. Consider Rapido Bike or public transport to bypass traffic."
        else:
            peak_label = "Evening Peak Hours"
            recommendation = "Office rush hour. Fares are higher; sharing or biking might save time."
        surge_multiplier = 1.3
    else:
        peak_label = "Off-Peak Hours"
        surge_multiplier = 1.0
        recommendation = "Normal traffic. Cabs should be readily available at standard rates."
        
    return {
        "is_peak": is_peak,
        "peak_label": peak_label,
        "surge_multiplier": surge_multiplier,
        "recommendation": recommendation
    }

def estimate_fare(distance_km: float, duration_minutes: float, is_raining: bool, current_hour: int) -> dict:
    """
    Calculates estimated cab fares across Ola Mini, Ola Auto, Uber Go, Uber Auto, Rapido Bike, and Rapido Auto.
    Surge rules:
      - Peak hour only (8-10 AM, 5-8 PM): 1.3x
      - Rain only: 1.2x
      - Both: 1.5x
    """
    # 1. Determine surge multiplier
    is_peak = (8 <= current_hour < 10) or (17 <= current_hour < 20)
    
    if is_peak and is_raining:
        surge = 1.5
        surge_applied = "Peak Hour & Rain (1.5x)"
    elif is_peak:
        surge = 1.3
        surge_applied = "Peak Hour (1.3x)"
    elif is_raining:
        surge = 1.2
        surge_applied = "Rain (1.2x)"
    else:
        surge = 1.0
        surge_applied = "None (1.0x)"

    # Base rates config
    # Base rates (per km) and base charge (minimum base fare):
    # Ola Mini: ₹12, base ₹30
    # Ola Auto: ₹10, base ₹25
    # Uber Go: ₹13, base ₹35
    # Uber Auto: ₹10, base ₹25
    # Rapido Bike: ₹6, base ₹15
    # Rapido Auto: ₹9, base ₹20
    providers_config = {
        "Ola Mini": {"rate": 12.0, "base": 30.0, "base_eta": 4.0},
        "Ola Auto": {"rate": 10.0, "base": 25.0, "base_eta": 3.0},
        "Uber Go": {"rate": 13.0, "base": 35.0, "base_eta": 5.0},
        "Uber Auto": {"rate": 10.0, "base": 25.0, "base_eta": 3.0},
        "Rapido Bike": {"rate": 6.0, "base": 15.0, "base_eta": 2.0},
        "Rapido Auto": {"rate": 9.0, "base": 20.0, "base_eta": 3.0},
    }
    
    fares = {}
    cheapest_provider = None
    cheapest_val = float('inf')
    
    fastest_provider = None
    fastest_eta = float('inf')
    
    for provider, cfg in providers_config.items():
        base = cfg["base"]
        rate = cfg["rate"]
        
        # Calculate fare before surge
        raw_fare = base + (distance_km * rate)
        # Apply surge
        surged_fare = raw_fare * surge
        
        # Min/max fare (give a range of +/- 7% to account for traffic variation)
        min_fare = max(base, round(surged_fare * 0.95))
        max_fare = max(base, round(surged_fare * 1.05))
        
        # Calculate dynamic ETA based on weather/traffic
        weather_delay = 3.0 if is_raining else 0.0
        traffic_delay = 4.0 if is_peak else 0.0
        eta = int(cfg["base_eta"] + weather_delay + traffic_delay)
        
        fares[provider] = {
            "min": min_fare,
            "max": max_fare,
            "eta": eta,
            "surge_applied": surge_applied
        }
        
        # Find cheapest based on min fare
        if min_fare < cheapest_val:
            cheapest_val = min_fare
            cheapest_provider = provider
            
        # Find fastest based on eta
        if eta < fastest_eta:
            fastest_eta = eta
            fastest_provider = provider
            
    return {
        "fares": fares,
        "cheapest": cheapest_provider,
        "fastest": fastest_provider
    }
