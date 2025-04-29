import pandas as pd
from shapely.geometry import Point
import requests
from io import StringIO
import json

# Load the data from the Gist
pedestrianCounts = requests.get("https://gist.githubusercontent.com/JoshBong/d83569f9837962d98b2c16d2312ed2d2/raw").text
p = "https://gist.githubusercontent.com/JoshBong/5e6697ffa29f3db776254188a5aea8fb/raw/6621a3cf7fcde270097be79a1b5fe5c5716ae618/gistfile1.txt"
neighborhoods_text = requests.get(p).text
# print(neighborhoods_text)
neighborhoods = json.loads(neighborhoods_text)
df = pd.read_csv(StringIO(pedestrianCounts))
# print(df['Loc'])
# print(neighborhoods.keys())

# Modify the parsing function to handle 'the_geom' column
def parse_geometry(geometry_str):
    try:
        # Extract LAT and LONG from the 'POINT (LAT LONG)' format
        coords = geometry_str.strip('POINT ()').split()
        lat, lon = round(float(coords[1]), 3), round(float(coords[0]), 3)  # LAT, LONG in correct order
        return lat, lon  # Return as tuple (lat, lon)
    except Exception as e:
        print(f"Error parsing geometry: {geometry_str}, Error: {e}")
        return None  # Return None for invalid data
    
# Apply the modified parsing function to the 'the_geom' column
df[['latitude', 'longitude']] = df['the_geom'].apply(lambda x: pd.Series(parse_geometry(x)))

# Check for any invalid geometry points
invalid_points = df[df[['latitude', 'longitude']].isnull().any(axis=1)]
# print(f"Invalid geometry points:\n{invalid_points}")

# Function to find the rent for a point based on its location
def assign_rent(lat, lon):
    for district, data in neighborhoods.items():
        # Check if the point is within the bounding box of the neighborhood
        if data['lat_min'] <= lat <= data['lat_max'] and data['lon_min'] <= lon <= data['lon_max']:
            return data['rent']  # Return the rent if the point is within the bounding box
    return None  # Return None if no match is found

# Apply the rent assignment
df['rent_per_sqft'] = df.apply(lambda row: assign_rent(row['latitude'], row['longitude']), axis=1)

print("Total rows:", len(df))
print("Rows with rent:", df['rent_per_sqft'].notnull().sum())
print("Rows without rent (NaN):", df['rent_per_sqft'].isnull().sum())
nan_rent_df = df[df['rent_per_sqft'].isnull()]
for index, row in nan_rent_df.iterrows():
    try:
        coords = row['the_geom'].strip('POINT ()').split()
        lon = round(float(coords[0]), 4)
        lat = round(float(coords[1]), 4)
        print(f"Index: {index}, Latitude: {lat}, Longitude: {lon}")
    except Exception as e:
        print(f"Index: {index}, Error parsing geometry: {row['the_geom']}")
# Set Pandas option to display all rows

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
# Check the updated DataFrame
print(df[['latitude', 'longitude', 'rent_per_sqft']].head())
pd.set_option('display.max_rows', 60)

# Print the row that has rent_per_sqft not NaN
# print(df[df['rent_per_sqft'].notnull()])
# print(df[df['rent_per_sqft'].isnull()])





