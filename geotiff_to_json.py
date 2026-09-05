import json
import argparse
try:
    import rasterio
    from rasterio.transform import rowcol
except ImportError:
    print("Please install rasterio: pip install rasterio")
    exit(1)

def extract_data(geotiff_path, locations, output_json):
    """
    Extracts pixel values from a GeoTiff at specific lat/lon coordinates
    and saves them to a JSON file.
    """
    results = {}
    
    print(f"Opening {geotiff_path}...")
    try:
        with rasterio.open(geotiff_path) as dataset:
            # Loop through our target locations
            for loc_name, coords in locations.items():
                lat, lon = coords["lat"], coords["lon"]
                
                # Convert lat/lon to row/col in the image matrix
                row, col = rowcol(dataset.transform, lon, lat)
                
                # Read the pixel value at that row/col from the first band
                # Assuming band 1 contains our data (e.g., Chlorophyll or SST)
                try:
                    value = dataset.read(1)[row, col]
                    # Convert numpy types to native python types for JSON serialization
                    value = float(value) 
                    
                    results[loc_name] = {
                        "lat": lat,
                        "lon": lon,
                        "value": value
                    }
                    print(f"Extracted {loc_name}: {value}")
                except IndexError:
                    print(f"Warning: Coordinates for {loc_name} ({lat}, {lon}) are outside the bounds of this GeoTiff.")
                    results[loc_name] = {
                        "lat": lat,
                        "lon": lon,
                        "error": "Out of bounds"
                    }
                    
    except Exception as e:
        print(f"Error reading GeoTiff: {e}")
        return

    # Write to JSON
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\nSuccessfully wrote extracted data to {output_json}")

if __name__ == "__main__":
    # Example usage. You will change these once you know your target region.
    # We will pick some arbitrary points off the coast of Gujarat as an example.
    target_locations = {
        "Zone_A_Nearshore": {"lat": 21.5, "lon": 69.0},
        "Zone_B_Offshore": {"lat": 21.0, "lon": 68.5},
        "Harbor_Point": {"lat": 22.0, "lon": 69.5}
    }
    
    # You will run the script like this: python geotiff_to_json.py your_downloaded_file.tif output_data.json
    parser = argparse.ArgumentParser(description="Extract points from GeoTiff")
    parser.add_argument("input_tif", help="Path to the downloaded GeoTiff file")
    parser.add_argument("output_json", help="Path to save the JSON output")
    args = parser.parse_args()
    
    extract_data(args.input_tif, args.output_json, target_locations)
