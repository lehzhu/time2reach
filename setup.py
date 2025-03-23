import os
import pandas as pd
import geopandas as gpd
import partridge as ptg
from shapely.geometry import Point
import pickle
import time
import numpy as np
from rtree import index

# Constants
MAX_WALKING_DISTANCE = 800  # meters

def preprocess_gtfs():
    """
    Preprocess the GTFS data for faster loading.
    Creates indices and caches calculated data.
    """
    print("Preprocessing GTFS data for London, Ontario...")
    start_time = time.time()
    
    gtfs_path = os.path.join('city-gtfs', 'london')
    
    # Load GTFS data
    feed = ptg.load_feed(gtfs_path)
    
    # Preprocess stops
    stops = feed.stops.copy()
    stops['geometry'] = [Point(lon, lat) for lon, lat in zip(stops.stop_lon, stops.stop_lat)]
    stops_gdf = gpd.GeoDataFrame(stops, geometry='geometry')
    
    # Create spatial index for fast nearest neighbor search
    idx = index.Index()
    for i, stop in stops.iterrows():
        idx.insert(i, (stop.stop_lon, stop.stop_lat, stop.stop_lon, stop.stop_lat))
    
    # Create stop distance matrix (for walking transfers)
    print("Creating stop transfer matrix...")
    transfer_matrix = {}
    
    for i, stop1 in stops.iterrows():
        # Get nearby stops within ~1km
        nearby = list(idx.intersection((
            stop1.stop_lon - 0.01, 
            stop1.stop_lat - 0.01, 
            stop1.stop_lon + 0.01, 
            stop1.stop_lat + 0.01
        )))
        
        transfers = []
        for j in nearby:
            if i == j:
                continue
                
            stop2 = stops.iloc[j]
            
            # Calculate distance in meters (approximate)
            dx = 111320 * np.cos(np.radians(stop1.stop_lat)) * (stop2.stop_lon - stop1.stop_lon)
            dy = 110540 * (stop2.stop_lat - stop1.stop_lat)
            distance = np.sqrt(dx*dx + dy*dy)
            
            if distance <= MAX_WALKING_DISTANCE:
                transfers.append({
                    'to_stop_id': stop2.stop_id,
                    'distance': distance,
                    'time_to_walk': distance / 1.25  # Using STRAIGHT_WALKING_SPEED
                })
                
        transfer_matrix[stop1.stop_id] = transfers
    
    # Convert stop_times departure_time to seconds for faster processing
    stop_times = feed.stop_times.copy()
    stop_times['departure_secs'] = stop_times['departure_time'].apply(
        lambda x: int(x.split(':')[0]) * 3600 + int(x.split(':')[1]) * 60 + int(x.split(':')[2])
    )
    stop_times['arrival_secs'] = stop_times['arrival_time'].apply(
        lambda x: int(x.split(':')[0]) * 3600 + int(x.split(':')[1]) * 60 + int(x.split(':')[2])
    )
    
    # Create cache directory if it doesn't exist
    if not os.path.exists('cache'):
        os.makedirs('cache')
    
    # Save preprocessed data
    preprocessed_data = {
        'stops': stops,
        'stops_gdf': stops_gdf,
        'spatial_index': idx,
        'transfer_matrix': transfer_matrix,
        'stop_times': stop_times,
        'routes': feed.routes,
        'trips': feed.trips,
        'calendar': feed.calendar,
        'calendar_dates': feed.calendar_dates
    }
    
    with open('cache/preprocessed_london.pickle', 'wb') as f:
        pickle.dump(preprocessed_data, f)
    
    print(f"Preprocessing completed in {time.time() - start_time:.2f} seconds")
    print(f"Results saved to cache/preprocessed_london.pickle")

if __name__ == "__main__":
    preprocess_gtfs() 