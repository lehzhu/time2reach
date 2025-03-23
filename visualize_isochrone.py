import os
import pandas as pd
import geopandas as gpd
import partridge as ptg
import numpy as np
from shapely.geometry import Point, LineString
from rtree import index
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import datetime
import time
import pickle
import json
import folium
from folium.plugins import HeatMap

# Constants
WALKING_SPEED = 1.42  # m/s
STRAIGHT_WALKING_SPEED = 1.25  # m/s
MIN_TRANSFER_SECONDS = 35.0
TRANSIT_EXIT_PENALTY = 10.0
MAX_WALKING_DISTANCE = 800  # meters

# Location parameters
LATITUDE = 43.00754265588104
LONGITUDE = -81.2764633569997
START_TIME = 8 * 3600  # 8:00 AM in seconds
DURATION = 3600  # 1 hour in seconds

def load_preprocessed_data():
    if os.path.exists('cache/preprocessed_london.pickle'):
        print("Loading preprocessed GTFS data...")
        with open('cache/preprocessed_london.pickle', 'rb') as f:
            data = pickle.load(f)
        return data
    else:
        print("No preprocessed data found. Running preprocessing...")
        # Import setup module 
        import setup
        setup.preprocess_gtfs()
        
        # Now load the preprocessed data
        with open('cache/preprocessed_london.pickle', 'rb') as f:
            data = pickle.load(f)
        return data

def find_nearest_stops(lat, lng, max_distance=MAX_WALKING_DISTANCE, gtfs_data=None):
    """Find stops within walking distance of a given location"""
    x, y = lng, lat
    
    # Get candidates from spatial index
    candidates = list(gtfs_data['spatial_index'].intersection((x-0.05, y-0.05, x+0.05, y+0.05)))
    
    # Filter by actual distance
    nearby_stops = []
    origin = Point(x, y)
    
    for i in candidates:
        stop = gtfs_data['stops'].iloc[i]
        stop_point = Point(stop.stop_lon, stop.stop_lat)
        
        # Calculate distance in meters (approximate)
        dx = 111320 * np.cos(np.radians(y)) * (stop.stop_lon - x)
        dy = 110540 * (stop.stop_lat - y)
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance <= max_distance:
            nearby_stops.append({
                'stop_id': stop.stop_id,
                'distance': distance,
                'time_to_walk': distance / STRAIGHT_WALKING_SPEED,
                'stop_name': stop.stop_name,
                'stop_lat': stop.stop_lat,
                'stop_lon': stop.stop_lon
            })
    
    return sorted(nearby_stops, key=lambda x: x['distance'])

def get_next_departures(stop_id, from_time, gtfs_data=None):
    """Get all trips departing from a stop after the given time"""
    # Get all stop times for this stop
    stop_departures = gtfs_data['stop_times'][gtfs_data['stop_times'].stop_id == stop_id].copy()
    
    # Filter departures after from_time
    stop_departures = stop_departures[stop_departures.departure_secs >= from_time]
    
    # Join with trips and routes
    departures = stop_departures.merge(gtfs_data['trips'], on='trip_id')
    departures = departures.merge(gtfs_data['routes'], on='route_id')
    
    # Sort by departure time
    departures = departures.sort_values('departure_secs')
    
    return departures

def get_trip_stops(trip_id, from_stop_sequence=0, gtfs_data=None):
    """Get all stops for a trip after the given stop sequence"""
    trip_stops = gtfs_data['stop_times'][gtfs_data['stop_times'].trip_id == trip_id].copy()
    trip_stops = trip_stops[trip_stops.stop_sequence > from_stop_sequence]
    trip_stops = trip_stops.sort_values('stop_sequence')
    
    # Add stop information
    trip_stops = trip_stops.merge(gtfs_data['stops'], on='stop_id')
    
    return trip_stops

def get_stop_transfers(stop_id, gtfs_data=None):
    """Get all transfers from a stop"""
    if 'transfer_matrix' in gtfs_data and stop_id in gtfs_data['transfer_matrix']:
        return gtfs_data['transfer_matrix'][stop_id]
    else:
        # Fallback to calculating transfers on the fly
        stop = gtfs_data['stops'][gtfs_data['stops'].stop_id == stop_id].iloc[0]
        return find_nearest_stops(stop.stop_lat, stop.stop_lon, gtfs_data=gtfs_data)

def service_runs_on_date(service_id, date, gtfs_data=None):
    """Check if a service runs on a given date"""
    # First check calendar
    service_calendar = gtfs_data['calendar'][gtfs_data['calendar'].service_id == service_id]
    
    if len(service_calendar) == 0:
        return False
    
    weekday = date.weekday()
    weekday_cols = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    if service_calendar.iloc[0][weekday_cols[weekday]] == 0:
        return False
    
    # Check date range
    start_date = pd.to_datetime(service_calendar.iloc[0].start_date, format='%Y%m%d')
    end_date = pd.to_datetime(service_calendar.iloc[0].end_date, format='%Y%m%d')
    
    if date < start_date or date > end_date:
        return False
    
    # Check exceptions in calendar_dates
    exceptions = gtfs_data['calendar_dates'][
        (gtfs_data['calendar_dates'].service_id == service_id) & 
        (gtfs_data['calendar_dates'].date == date.strftime('%Y%m%d'))
    ]
    
    if len(exceptions) > 0:
        # 1 means service added, 2 means service removed
        return exceptions.iloc[0].exception_type == 1
    
    return True

def calculate_isochrone(lat, lng, start_time_seconds, duration_seconds, transfer_penalty=60, gtfs_data=None):
    """
    Calculate the isochrone map from a given location, start time, and duration.
    Returns a mapping of edge_ids to travel times and reachable stops.
    """
    start_location = Point(lng, lat)
    
    # Find stops within walking distance
    nearby_stops = find_nearest_stops(lat, lng, gtfs_data=gtfs_data)
    
    # Initialize with initial location
    queue = []
    visited_stops = {}
    edge_times = {}
    reachable_stops = []  # Will store tuples of (stop_lat, stop_lon, travel_time)
    
    date = datetime.now().date()
    
    # Add initial nearby stops to queue
    for stop in nearby_stops:
        arrival_time = start_time_seconds + stop['time_to_walk']
        stop_id = stop['stop_id']
        
        if arrival_time <= start_time_seconds + duration_seconds:
            visited_stops[stop_id] = {
                'time': arrival_time,
                'transfers': 0,
                'previous_trip': None,
                'previous_stop': None,
                'walking_distance': stop['distance']
            }
            
            # Add stop to results
            edge_id = f"s{stop_id}"
            edge_times[edge_id] = int(arrival_time - start_time_seconds)
            
            # Add to reachable stops
            reachable_stops.append((stop['stop_lat'], stop['stop_lon'], arrival_time - start_time_seconds))
            
            # Get next departures from this stop
            departures = get_next_departures(stop_id, arrival_time, gtfs_data=gtfs_data)
            
            for _, departure in departures.iterrows():
                service_id = departure['service_id']
                
                # Check if service runs today
                if not service_runs_on_date(service_id, date, gtfs_data=gtfs_data):
                    continue
                
                # Add to exploration queue
                queue.append({
                    'stop_id': stop_id,
                    'trip_id': departure['trip_id'],
                    'route_id': departure['route_id'],
                    'departure_time': departure['departure_secs'],
                    'stop_sequence': departure['stop_sequence'],
                    'transfers': 0,
                    'previous_trip': None,
                    'previous_stop': None
                })
    
    # Process queue
    while queue:
        # Get next item with earliest departure time
        current = min(queue, key=lambda x: x['departure_time'])
        queue.remove(current)
        
        stop_id = current['stop_id']
        trip_id = current['trip_id']
        current_time = current['departure_time']
        
        if current_time > start_time_seconds + duration_seconds:
            continue
        
        # Get all stops for this trip
        trip_stops = get_trip_stops(trip_id, current['stop_sequence'], gtfs_data=gtfs_data)
        
        # Add each reachable stop
        for _, stop in trip_stops.iterrows():
            arrival_time = stop['arrival_secs']
            
            next_stop_id = stop['stop_id']
            next_stop_key = f"t{trip_id}_{next_stop_id}"
            
            # If arrival is beyond our timeframe, skip
            if arrival_time > start_time_seconds + duration_seconds:
                continue
            
            # Add to edge times
            if next_stop_key not in edge_times or edge_times[next_stop_key] > arrival_time - start_time_seconds:
                edge_times[next_stop_key] = int(arrival_time - start_time_seconds)
                # Add to reachable stops
                reachable_stops.append((stop.stop_lat, stop.stop_lon, arrival_time - start_time_seconds))
            
            # Check if this is the first time or a faster time to this stop
            if next_stop_id not in visited_stops or arrival_time < visited_stops[next_stop_id]['time']:
                visited_stops[next_stop_id] = {
                    'time': arrival_time,
                    'transfers': current['transfers'],
                    'previous_trip': trip_id,
                    'previous_stop': stop_id,
                    'walking_distance': 0
                }
                
                # Find transfers from this stop
                transfers = get_stop_transfers(next_stop_id, gtfs_data=gtfs_data)
                
                for transfer_stop in transfers:
                    transfer_stop_id = transfer_stop['stop_id']
                    transfer_time = arrival_time + transfer_stop['time_to_walk'] + MIN_TRANSFER_SECONDS
                    
                    if transfer_time <= start_time_seconds + duration_seconds:
                        # Get departures from transfer stop
                        transfer_departures = get_next_departures(transfer_stop_id, transfer_time, gtfs_data=gtfs_data)
                        
                        for _, departure in transfer_departures.iterrows():
                            service_id = departure['service_id']
                            
                            # Check if service runs today
                            if not service_runs_on_date(service_id, date, gtfs_data=gtfs_data):
                                continue
                            
                            # Add transfer penalty if it's not the same route
                            effective_departure_time = departure['departure_secs']
                            if departure['route_id'] != current['route_id']:
                                effective_departure_time += transfer_penalty
                            
                            # Add to exploration queue if within time window
                            if effective_departure_time <= start_time_seconds + duration_seconds:
                                queue.append({
                                    'stop_id': transfer_stop_id,
                                    'trip_id': departure['trip_id'],
                                    'route_id': departure['route_id'],
                                    'departure_time': effective_departure_time,
                                    'stop_sequence': departure['stop_sequence'],
                                    'transfers': current['transfers'] + 1,
                                    'previous_trip': trip_id,
                                    'previous_stop': next_stop_id
                                })
    
    return edge_times, reachable_stops

def create_folium_map(lat, lng, reachable_stops):
    """Create a Folium map visualization of the isochrone"""
    print(f"Creating map visualization for {lat}, {lng}...")
    
    # Create a map centered at the origin
    m = folium.Map(location=[lat, lng], zoom_start=13)
    
    # Add a marker for the origin
    folium.Marker(
        [lat, lng],
        popup="Origin",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)
    
    # Normalize times for coloring
    max_time = max([time for _, _, time in reachable_stops])
    
    # Group stops by travel time into buckets (15-minute intervals)
    time_buckets = {
        "0-15 min": [],
        "15-30 min": [],
        "30-45 min": [],
        "45-60 min": [],
    }
    
    for stop_lat, stop_lon, time in reachable_stops:
        minutes = time / 60
        if minutes <= 15:
            color = "green"
            bucket = "0-15 min"
        elif minutes <= 30:
            color = "blue"
            bucket = "15-30 min"
        elif minutes <= 45:
            color = "purple"
            bucket = "30-45 min"
        else:
            color = "red"
            bucket = "45-60 min"
        
        time_buckets[bucket].append([stop_lat, stop_lon])
    
    # Create feature groups for each time bucket
    for bucket, stops in time_buckets.items():
        if not stops:
            continue
            
        fg = folium.FeatureGroup(name=bucket)
        
        for stop_lat, stop_lon in stops:
            folium.CircleMarker(
                location=[stop_lat, stop_lon],
                radius=4,
                popup=f"Travel time: {bucket}",
                color=color,
                fill=True,
                fill_opacity=0.7
            ).add_to(fg)
        
        fg.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the map
    map_file = f"isochrone_map_{lat}_{lng}.html"
    m.save(map_file)
    print(f"Map saved to {map_file}")
    
    return map_file

def create_heat_map(lat, lng, reachable_stops):
    """Create a heat map visualization of the isochrone"""
    print(f"Creating heat map visualization for {lat}, {lng}...")
    
    # Create a map centered at the origin
    m = folium.Map(location=[lat, lng], zoom_start=13)
    
    # Add a marker for the origin
    folium.Marker(
        [lat, lng],
        popup="Origin",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)
    
    # Prepare data for heatmap - invert times so closer = hotter
    max_time = max([time for _, _, time in reachable_stops])
    heat_data = [[stop_lat, stop_lon, 1 - (time / max_time)] for stop_lat, stop_lon, time in reachable_stops]
    
    # Add the heatmap
    HeatMap(heat_data, radius=15, blur=10, gradient={0.4: 'blue', 0.65: 'lime', 0.8: 'yellow', 1: 'red'}).add_to(m)
    
    # Save the map
    heat_map_file = f"isochrone_heatmap_{lat}_{lng}.html"
    m.save(heat_map_file)
    print(f"Heat map saved to {heat_map_file}")
    
    return heat_map_file

def main():
    """Main function to visualize isochrone from specified location"""
    print(f"Calculating isochrone from {LATITUDE}, {LONGITUDE}...")
    
    # Load data
    gtfs_data = load_preprocessed_data()
    
    # Calculate isochrone
    start_time = time.time()
    edge_times, reachable_stops = calculate_isochrone(
        LATITUDE, LONGITUDE, START_TIME, DURATION, 
        transfer_penalty=60, gtfs_data=gtfs_data
    )
    print(f"Calculation took {time.time() - start_time:.2f} seconds")
    print(f"Found {len(reachable_stops)} reachable stops")
    
    # Create visualizations
    map_file = create_folium_map(LATITUDE, LONGITUDE, reachable_stops)
    heat_map_file = create_heat_map(LATITUDE, LONGITUDE, reachable_stops)
    
    print(f"\nVisualization complete! Open these files in your browser:")
    print(f"1. Marker Map: {map_file}")
    print(f"2. Heat Map: {heat_map_file}")

if __name__ == "__main__":
    main() 