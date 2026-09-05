import json
import argparse
try:
    import xarray as xr
except ImportError:
    print("Please install required libraries: pip install xarray netCDF4")
    exit(1)

def extract_data(netcdf_path, locations, output_json, variable_name):
    """
    Extracts data values from a NetCDF file at specific lat/lon coordinates
    and saves them to a JSON file.
    """
    results = {}
    
    print(f"Opening {netcdf_path}...")
    try:
        # Open the dataset
        ds = xr.open_dataset(netcdf_path)
        
        # Print available variables so the user knows what they can extract
        print(f"Available variables in this NetCDF: {list(ds.data_vars)}")
        
        if variable_name not in ds.data_vars:
            print(f"Error: Variable '{variable_name}' not found in the dataset.")
            return

        for loc_name, coords in locations.items():
            target_lat, target_lon = coords["lat"], coords["lon"]
            
            try:
                # Use xarray's powerful nearest-neighbor selection
                # We assume the dimensions are named 'lat' and 'lon'. 
                # If they are named 'latitude'/'longitude' in the specific file, xarray will need adjustment.
                
                # Check dimension names
                lat_dim = 'lat' if 'lat' in ds.dims else 'latitude'
                lon_dim = 'lon' if 'lon' in ds.dims else 'longitude'
                
                if lat_dim not in ds.dims or lon_dim not in ds.dims:
                    print(f"Warning: Standard lat/lon dimensions not found. Dimensions are: {list(ds.dims)}")
                    
                # Extract the nearest point
                point_data = ds[variable_name].sel({lat_dim: target_lat, lon_dim: target_lon}, method='nearest')
                
                # If there's a time dimension, take the first/latest one for the MVP
                if 'time' in point_data.dims:
                    value = float(point_data.isel(time=0).values)
                else:
                    value = float(point_data.values)

                results[loc_name] = {
                    "lat": target_lat,
                    "lon": target_lon,
                    "value": value,
                    "variable": variable_name
                }
                print(f"Extracted {loc_name}: {value}")
                
            except Exception as e:
                print(f"Warning: Could not extract data for {loc_name}: {e}")
                results[loc_name] = {
                    "lat": target_lat,
                    "lon": target_lon,
                    "error": str(e)
                }

    except Exception as e:
        print(f"Error reading NetCDF: {e}")
        return

    # Write to JSON
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\nSuccessfully wrote extracted data to {output_json}")

if __name__ == "__main__":
    # Example locations off the coast of India
    target_locations = {
        "Zone_A_Nearshore": {"lat": 21.5, "lon": 69.0},
        "Zone_B_Offshore": {"lat": 21.0, "lon": 68.5},
        "Harbor_Point": {"lat": 22.0, "lon": 69.5}
    }
    
    parser = argparse.ArgumentParser(description="Extract points from NetCDF")
    parser.add_argument("input_nc", help="Path to the downloaded .nc file")
    parser.add_argument("output_json", help="Path to save the JSON output")
    parser.add_argument("variable", help="The name of the variable to extract (e.g., 'sst', 'chlor_a')")
    args = parser.parse_args()
    
    extract_data(args.input_nc, args.output_json, target_locations, args.variable)
