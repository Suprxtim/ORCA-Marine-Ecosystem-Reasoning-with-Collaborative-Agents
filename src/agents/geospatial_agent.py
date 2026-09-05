import json
import os
from shapely.geometry import Point, shape
from pyproj import Geod
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

# Load data once at startup
GEOJSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_geofence_data.geojson")
geofence_features = []

if os.path.exists(GEOJSON_PATH):
    with open(GEOJSON_PATH, "r") as f:
        data = json.load(f)
        for feature in data.get("features", []):
            geom = shape(feature["geometry"])
            geofence_features.append({
                "geometry": geom,
                "zone_type": feature["properties"].get("zone_type"),
                "zone_name": feature["properties"].get("zone_name")
            })

geod = Geod(ellps="WGS84")

def calculate_distance_km(point1: Point, geom2) -> float:
    """Calculate shortest distance in km between a point and a geometry."""
    # Find the nearest point on geom2 to point1
    # shapely distance is Euclidean. For WGS84, we approximate using pyproj on the nearest coordinates
    from shapely.ops import nearest_points
    p1, p2 = nearest_points(point1, geom2)
    _, _, distance_m = geod.inv(p1.x, p1.y, p2.x, p2.y)
    return distance_m / 1000.0

@tool
def check_geofence(latitude: float, longitude: float) -> str:
    """
    Checks if a given latitude and longitude intersects with any restricted marine zones (MPA, IMBL, restricted_waters).
    Returns a JSON string containing the structured result.
    """
    point = Point(longitude, latitude)
    
    inside_zone = False
    zone_type = None
    zone_name = None
    min_dist_km = float('inf')
    nearest_type = None

    for f in geofence_features:
        geom = f["geometry"]
        # Check intersection
        if geom.contains(point) or geom.intersects(point):
            inside_zone = True
            zone_type = f["zone_type"]
            zone_name = f["zone_name"]
            min_dist_km = 0.0
            nearest_type = zone_type
            break
            
        # If not inside, calculate distance to this feature
        dist = calculate_distance_km(point, geom)
        if dist < min_dist_km:
            min_dist_km = dist
            nearest_type = f["zone_type"]

    result = {
        "inside_restricted_zone": inside_zone,
        "zone_type": zone_type,
        "zone_name": zone_name,
        "distance_to_nearest_boundary_km": round(min_dist_km, 2) if min_dist_km != float('inf') else 999.9,
        "nearest_zone_type": nearest_type
    }
    
    return json.dumps(result)

def get_geospatial_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, max_tokens=800).with_config(tags=["geospatial_llm"])
    
    prompt = """You are the Geospatial/Geofencing Agent. Your job is to check if the user's location is inside or near any restricted marine zones (like MPAs or the IMBL). 
Call your check_geofence tool with the coordinates extracted from the conversation. 
When the tool returns its JSON, YOUR FINAL RESPONSE MUST BE THE EXACT, UNMODIFIED JSON STRING. 
CRITICAL: Do NOT truncate strings. Do NOT add spaces. Do NOT shorten names like "Gulf of Kutch Marine Sanctuary". Output the exact JSON directly."""
    
    return create_react_agent(
        llm,
        tools=[check_geofence],
        prompt=prompt
    )
