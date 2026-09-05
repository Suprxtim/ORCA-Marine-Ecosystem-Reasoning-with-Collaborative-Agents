import json
import os
import math
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# Get the path to the Desktop/ORCA folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points on the earth."""
    R = 6371.0 # Earth radius in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class LocationInput(BaseModel):
    location_name: Optional[str] = Field(None, description="Name of the location to look up, e.g. 'Harbor_Point'")
    latitude: Optional[float] = Field(None, description="Latitude of the location")
    longitude: Optional[float] = Field(None, description="Longitude of the location")

def resolve_location(data: dict, location_name: str = None, lat: float = None, lon: float = None):
    locations = data.get("locations", {})
    
    # 1. Exact string match if provided
    if location_name and location_name in locations:
        return location_name, locations[location_name], 0.0
        
    # 2. Coordinate-based nearest neighbor if lat/lon provided
    if lat is not None and lon is not None:
        closest_name = None
        closest_data = None
        min_distance = float('inf')
        
        for name, loc_data in locations.items():
            loc_lat = loc_data.get("lat")
            loc_lon = loc_data.get("lon")
            if loc_lat is not None and loc_lon is not None:
                dist = haversine_distance(lat, lon, loc_lat, loc_lon)
                if dist < min_distance:
                    min_distance = dist
                    closest_name = name
                    closest_data = loc_data
                    
        if closest_name and min_distance <= 50.0:
            return closest_name, closest_data, round(min_distance, 2)
        elif closest_name:
            return None, None, round(min_distance, 2)
            
    return None, None, None

async def get_weather_data(location_name: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
    """Retrieve wave height, wind speed, lightning risk, and cyclone alerts."""
    if not location_name and (latitude is None or longitude is None):
        return "Error: Must provide either location_name OR both latitude and longitude."
        
    file_path = os.path.join(BASE_DIR, "mock_weather_data.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            
        matched_name, loc_data, dist_km = resolve_location(data, location_name, latitude, longitude)
        
        result = {}
        fetch_lat = latitude if latitude is not None else (loc_data.get("lat") if loc_data else None)
        fetch_lon = longitude if longitude is not None else (loc_data.get("lon") if loc_data else None)
        
        if fetch_lat is not None and fetch_lon is not None:
            import requests
            wind_url = f"https://api.open-meteo.com/v1/forecast?latitude={fetch_lat}&longitude={fetch_lon}&current=wind_speed_10m&wind_speed_unit=kn"
            wave_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={fetch_lat}&longitude={fetch_lon}&current=wave_height"
            
            try:
                wind_res = requests.get(wind_url).json()
                wave_res = requests.get(wave_url).json()
                result["wind_speed_knots"] = wind_res.get("current", {}).get("wind_speed_10m", "N/A")
                result["wind_source"] = "live"
                result["wave_height_meters"] = wave_res.get("current", {}).get("wave_height", "N/A")
                result["wave_source"] = "live"
            except Exception as e:
                result["wind_speed_knots"] = "Error fetching live data"
                result["wave_height_meters"] = "Error fetching live data"
        else:
            result["wind_speed_knots"] = loc_data.get("wind_speed_knots") if loc_data else "N/A"
            result["wind_source"] = "reference_data"
            result["wave_height_meters"] = loc_data.get("wave_height_meters") if loc_data else "N/A"
            result["wave_source"] = "reference_data"

        if loc_data:
            result["cyclone_alert"] = loc_data.get("cyclone_alert")
            result["cyclone_source"] = "reference_data"
            result["lightning_risk"] = loc_data.get("lightning_risk")
            result["lightning_source"] = "reference_data"
            
            if dist_km is not None and dist_km > 20.0:
                result["cyclone_low_confidence"] = True
                result["lightning_low_confidence"] = True
                
            result["matched_location"] = matched_name
            result["distance_km"] = dist_km
        else:
            result["cyclone_alert"] = "No reference data"
            result["cyclone_source"] = "reference_data"
            result["lightning_risk"] = "No reference data"
            result["lightning_source"] = "reference_data"
            
        return json.dumps(result)
    except Exception as e:
        return f"Error reading weather data: {str(e)}"

weather_tool = StructuredTool.from_function(
    func=get_weather_data,
    name="get_weather_data",
    description="Get wind, wave, and hazard data for a location by name or coordinates.",
    args_schema=LocationInput,
    coroutine=get_weather_data
)

async def get_marine_data(location_name: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
    """Retrieve Sea Surface Temperature, Chlorophyll, and PFZ status."""
    if not location_name and (latitude is None or longitude is None):
        return "Error: Must provide either location_name OR both latitude and longitude."
        
    file_path = os.path.join(BASE_DIR, "mock_marine_data.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            
        matched_name, loc_data, dist_km = resolve_location(data, location_name, latitude, longitude)
        
        result = {}
        fetch_lat = latitude if latitude is not None else (loc_data.get("lat") if loc_data else None)
        fetch_lon = longitude if longitude is not None else (loc_data.get("lon") if loc_data else None)
        
        if fetch_lat is not None and fetch_lon is not None:
            import requests
            temp_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={fetch_lat}&longitude={fetch_lon}&current=ocean_temperature"
            try:
                temp_res = requests.get(temp_url).json()
                result["sst_celsius"] = temp_res.get("current", {}).get("ocean_temperature", "N/A")
                result["sst_source"] = "live"
            except Exception as e:
                result["sst_celsius"] = "Error fetching live data"
                result["sst_source"] = "live"
        else:
            result["sst_celsius"] = loc_data.get("sst_celsius") if loc_data else "N/A"
            result["sst_source"] = "reference_data"

        if loc_data:
            result["chlorophyll_mg_m3"] = loc_data.get("chlorophyll_mg_m3")
            result["chlorophyll_source"] = "reference_data"
            result["is_pfz"] = loc_data.get("is_pfz")
            result["pfz_source"] = "reference_data"
            
            if dist_km is not None and dist_km > 20.0:
                result["chlorophyll_low_confidence"] = True
                result["pfz_low_confidence"] = True
                
            result["matched_location"] = matched_name
            result["distance_km"] = dist_km
        else:
            result["chlorophyll_mg_m3"] = "No reference data"
            result["chlorophyll_source"] = "reference_data"
            result["is_pfz"] = "No reference data"
            result["pfz_source"] = "reference_data"
            
        return json.dumps(result)
    except Exception as e:
        return f"Error reading marine data: {str(e)}"

marine_tool = StructuredTool.from_function(
    func=get_marine_data,
    name="get_marine_data",
    description="Get SST, Chlorophyll, and Potential Fishing Zone (PFZ) status by name or coordinates.",
    args_schema=LocationInput,
    coroutine=get_marine_data
)
