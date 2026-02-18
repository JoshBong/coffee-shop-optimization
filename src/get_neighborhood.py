import pandas as pd
from shapely.geometry import Point
import requests
from io import StringIO
import json


def get_neighborhoods(pedestrian_counts_url, neighborhoods_url):

    '''
    pedestrian count: csv of pedestrian counts
    neighborhood data: txt of neighborhood bounds 
    and accompanying rent data
    
    imports the pedestrian data and assigns rent values
    based on the lat and lon of the points
    '''

    # load the data from gist
    df = pd.read_csv(StringIO(requests.get(pedestrian_counts_url).text))
    # print(df)
    neighborhoods = json.loads(requests.get(neighborhoods_url).text)

    def get_lat_lon(point):
        '''
        turns the POINT('lat lon') column into a float lat/lon variable
        '''
        # print(point)
        coords = point.strip('POINT ()').split()
        lat, lon = round(float(coords[1]), 3), round(float(coords[0]), 3)
        return lat, lon

    # adds latitude and longitude column to the df as floats
    df[['latitude', 'longitude']] = df['the_geom'].apply(lambda x: pd.Series(get_lat_lon(x)))
    # print(df)

    def assign_rent(lat, lon):
        '''
        assigns the avg rent per sqft depending on the lat/long
        that the point is located in
        '''

        for area, data in neighborhoods.items():
            if data['lat_min'] <= lat <= data['lat_max'] and data['lon_min'] <= lon <= data['lon_max']:
                return data['rent']
        return None
    
    df['rent_per_sqft'] = df.apply(lambda row: assign_rent(row['latitude'], row['longitude']), axis=1)
    # print(df[['latitude', 'longitude', 'rent_per_sqft']])

    return df


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# df = get_neighborhoods(pedestrian_counts_url, neighborhoods_url)
# print(df[['latitude', 'longitude', 'rent_per_sqft']])