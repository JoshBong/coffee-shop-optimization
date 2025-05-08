# create_map.py
import folium
import pandas as pd
from typing import Union, Set, List
from get_neighborhood import get_neighborhoods
from optimization import prepare_data, optimize_coffee_shops

def create_map(
    all_locations_df: pd.DataFrame,
    profitable_locations: Union[Set[int], List[int]],
    output_file: str = "coffee_shop_locations.html",
    profit_data: pd.DataFrame = None,
    tile_style: str = "OpenStreetMap",
    min_zoom: int = 10,
    max_zoom: int = 18
) -> None:
    """
    Creates an interactive folium map highlighting profitable coffee shop locations.
    
    Args:
        all_locations_df: DataFrame containing location data with columns:
                         - 'Loc' (location ID)
                         - 'latitude'
                         - 'longitude'
                         - (optional) other columns for tooltip info
        profitable_locations: Collection of location IDs considered profitable
        output_file: Path to save the HTML map file
        profit_data: Optional DataFrame with profit information (must include 'Loc' column)
        tile_style: Map tile style (e.g., "OpenStreetMap", "Stamen Terrain", "CartoDB positron")
        min_zoom: Minimum zoom level
        max_zoom: Maximum zoom level
    """
    # Validate input data
    required_columns = {'Loc', 'latitude', 'longitude'}
    if not required_columns.issubset(all_locations_df.columns):
        missing = required_columns - set(all_locations_df.columns)
        raise ValueError(f"Input DataFrame missing required columns: {missing}")

    # Convert profitable_locations to set for faster lookup
    profitable_set = set(profitable_locations)
    
    # Create base map with better defaults
    nyc_center = [
        all_locations_df['latitude'].mean(),
        all_locations_df['longitude'].mean()
    ]
    
    m = folium.Map(
        location=nyc_center,
        zoom_start=12,
        tiles=None,  # Start with no tiles
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        control_scale=True
    )
    
    # Add tile layers with proper attribution
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        attr='© OpenStreetMap contributors'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='Stamen Terrain',
        name='Stamen Terrain',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'
    ).add_to(m)
    
    # Add layer control
    feature_group_profitable = folium.FeatureGroup(name="Optimal Locations (>$500/day)")
    feature_group_other = folium.FeatureGroup(name="All Locations")
    
    # Merge profit data if provided
    if profit_data is not None and 'Loc' in profit_data.columns:
        all_locations_df = all_locations_df.merge(
            profit_data,
            on='Loc',
            how='left'
        )
    
    # Add markers with enhanced tooltips
    for _, row in all_locations_df.iterrows():
        location_id = row['Loc']
        lat, lon = row['latitude'], row['longitude']
        
        # Prepare tooltip content
        tooltip_content = f"<b>Location ID:</b> {location_id}<br>"
        
        # Add additional info if available
        additional_fields = ['daily_avg', 'rent_per_sqft', 'Daily Profit', 'Operating Times', 'Daily Customers']
        for field in additional_fields:
            if field in row:
                value = row[field]
                if isinstance(value, (int, float)):
                    value = f"{value:,.2f}"
                tooltip_content += f"<b>{field.replace('_', ' ').title()}:</b> {value}<br>"
        
        # Create marker - all locations are blue now
        is_profitable = location_id in profitable_set
        radius = 5  # Smaller size
        fill_opacity = 0.9  # More solid
        
        marker = folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color='#2B4C7E',  # Muted navy blue
            weight=1.5,
            fill=True,
            fill_color='#2B4C7E',  # Same muted navy blue
            fill_opacity=fill_opacity,
            tooltip=tooltip_content,
            popup=f"Location {location_id}",
        )
        
        # Add to appropriate feature group
        if is_profitable:
            marker.add_to(feature_group_profitable)
        else:
            marker.add_to(feature_group_other)
    
    # Add feature groups to map
    feature_group_profitable.add_to(m)
    feature_group_other.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = '''
        <h3 align="center" style="font-size:16px">
            <b>Optimal Coffee Shop Locations</b><br>
            Use the layer control (top right) to toggle between profitable and other locations
        </h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    print(f"Map successfully saved to {output_file}")

# Example usage with optimization results
if __name__ == "__main__":
    try:
        # URLs for data
        pedestrian_url = "https://gist.githubusercontent.com/JoshBong/d83569f9837962d98b2c16d2312ed2d2/raw"
        neighborhoods_url = "https://gist.githubusercontent.com/JoshBong/5e6697ffa29f3db776254188a5aea8fb/raw/6621a3cf7fcde270097be79a1b5fe5c5716ae618/gistfile1.txt"
        
        # Get all locations data
        all_locations_df = get_neighborhoods(pedestrian_url, neighborhoods_url)
        
        # Get optimized locations
        df_processed = prepare_data(pedestrian_url, neighborhoods_url)
        optimal_locations = optimize_coffee_shops(df_processed)
        
        if optimal_locations is not None:
            # Get the profitable location IDs
            profitable_locs = set(optimal_locations['Location'])
            
            # Generate the map
            create_map(
                all_locations_df=all_locations_df,
                profitable_locations=profitable_locs,
                profit_data=optimal_locations,
                output_file="coffee_shop_locations.html",
                tile_style="Stamen Terrain"
            )
            
            print("Map generated with optimization results")
            print(f"Found {len(profitable_locs)} profitable locations")
        else:
            print("No optimal solutions found")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise