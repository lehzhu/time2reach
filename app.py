from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import geopandas as gpd
import partridge as ptg
import numpy as np
from shapely.geometry import Point, LineString
from rtree import index
import os
from datetime import datetime, timedelta
import time
import json
import pickle

app = Flask(__name__)
CORS(app)

# Constants
WALKING_SPEED = 1.42  # m/s
STRAIGHT_WALKING_SPEED = 1.25  # m/s
MIN_TRANSFER_SECONDS = 35.0
TRANSIT_EXIT_PENALTY = 10.0
MAX_WALKING_DISTANCE = 800  # meters

# Load preprocessed GTFS data
def load_preprocessed_data():
    if os.path.exists('cache/preprocessed_london.pickle'):
        print("Loading preprocessed GTFS data...")
        with open('cache/preprocessed_london.pickle', 'rb') as f:
            data = pickle.load(f)
        return data
    else:
        print("No preprocessed data found. Loading raw GTFS data...")
        gtfs_path = os.path.join('city-gtfs', 'london')
        feed = ptg.load_feed(gtfs_path)
        
        stops = feed.stops.copy()
        routes = feed.routes.copy()
        trips = feed.trips.copy()
        stop_times = feed.stop_times.copy()
        calendar = feed.calendar.copy()
        calendar_dates = feed.calendar_dates.copy()
        
        # Add geometry to stops
        stops['geometry'] = [Point(lon, lat) for lon, lat in zip(stops.stop_lon, stops.stop_lat)]
        stops_gdf = gpd.GeoDataFrame(stops, geometry='geometry')
        
        # Create spatial index for fast nearest neighbor search
        idx = index.Index()
        for i, stop in stops.iterrows():
            idx.insert(i, (stop.stop_lon, stop.stop_lat, stop.stop_lon, stop.stop_lat))
        
        # Convert stop_times departure_time to seconds for faster processing
        stop_times['departure_secs'] = stop_times['departure_time'].apply(
            lambda x: int(x.split(':')[0]) * 3600 + int(x.split(':')[1]) * 60 + int(x.split(':')[2])
        )
        stop_times['arrival_secs'] = stop_times['arrival_time'].apply(
            lambda x: int(x.split(':')[0]) * 3600 + int(x.split(':')[1]) * 60 + int(x.split(':')[2])
        )
        
        # Basic transfer matrix
        transfer_matrix = {}
        
        return {
            'stops': stops,
            'stops_gdf': stops_gdf,
            'spatial_index': idx,
            'transfer_matrix': transfer_matrix,
            'stop_times': stop_times,
            'routes': routes,
            'trips': trips,
            'calendar': calendar,
            'calendar_dates': calendar_dates
        }

gtfs_data = load_preprocessed_data()

def find_nearest_stops(lat, lng, max_distance=MAX_WALKING_DISTANCE):
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

def get_next_departures(stop_id, from_time):
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

def get_trip_stops(trip_id, from_stop_sequence=0):
    """Get all stops for a trip after the given stop sequence"""
    trip_stops = gtfs_data['stop_times'][gtfs_data['stop_times'].trip_id == trip_id].copy()
    trip_stops = trip_stops[trip_stops.stop_sequence > from_stop_sequence]
    trip_stops = trip_stops.sort_values('stop_sequence')
    
    # Add stop information
    trip_stops = trip_stops.merge(gtfs_data['stops'], on='stop_id')
    
    return trip_stops

def get_stop_transfers(stop_id):
    """Get all transfers from a stop"""
    if 'transfer_matrix' in gtfs_data and stop_id in gtfs_data['transfer_matrix']:
        return gtfs_data['transfer_matrix'][stop_id]
    else:
        # Fallback to calculating transfers on the fly
        stop = gtfs_data['stops'][gtfs_data['stops'].stop_id == stop_id].iloc[0]
        return find_nearest_stops(stop.stop_lat, stop.stop_lon)

def service_runs_on_date(service_id, date):
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

def calculate_isochrone(lat, lng, start_time_seconds, duration_seconds, transfer_penalty=60):
    """
    Calculate the isochrone map from a given location, start time, and duration.
    Returns a mapping of edge_ids to travel times.
    """
    start_location = Point(lng, lat)
    
    # Find stops within walking distance
    nearby_stops = find_nearest_stops(lat, lng)
    
    # Initialize with initial location
    queue = []
    visited_stops = {}
    edge_times = {}
    
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
            
            # Get next departures from this stop
            departures = get_next_departures(stop_id, arrival_time)
            
            for _, departure in departures.iterrows():
                service_id = departure['service_id']
                
                # Check if service runs today
                if not service_runs_on_date(service_id, date):
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
        trip_stops = get_trip_stops(trip_id, current['stop_sequence'])
        
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
                transfers = get_stop_transfers(next_stop_id)
                
                for transfer_stop in transfers:
                    transfer_stop_id = transfer_stop['stop_id']
                    transfer_time = arrival_time + transfer_stop['time_to_walk'] + MIN_TRANSFER_SECONDS
                    
                    if transfer_time <= start_time_seconds + duration_seconds:
                        # Get departures from transfer stop
                        transfer_departures = get_next_departures(transfer_stop_id, transfer_time)
                        
                        for _, departure in transfer_departures.iterrows():
                            service_id = departure['service_id']
                            
                            # Check if service runs today
                            if not service_runs_on_date(service_id, date):
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
    
    return edge_times

@app.route('/api/v2/hello/', methods=['POST'])
def hello():
    data = request.json
    lat = data.get('latitude')
    lng = data.get('longitude')
    start_time = data.get('startTime', 8 * 3600)  # Default to 8:00 AM
    max_search_time = data.get('maxSearchTime', 3600)  # Default to 1 hour
    transfer_penalty = data.get('transferPenaltySecs', 60)  # Default to 60 seconds
    
    # Validate location is in London, Ontario region (approximate bounding box)
    if not (42.9 <= lat <= 43.1 and -81.4 <= lng <= -81.1):
        return jsonify({
            "error": "Invalid city - only London, Ontario is supported"
        }), 400
    
    # Calculate isochrone
    start = time.time()
    edge_times = calculate_isochrone(lat, lng, start_time, max_search_time, transfer_penalty)
    print(f"Calculation took {time.time() - start:.2f} seconds")
    
    # Generate a request ID
    request_id = {
        "rs_list_index": int(time.time()),
        "city": "London"
    }
    
    return jsonify({
        "request_id": request_id,
        "edge_times": edge_times
    })

@app.route('/api/v2/details/', methods=['POST'])
def details():
    data = request.json
    lat_lng = data.get('latlng', {})
    lat = lat_lng.get('latitude')
    lng = lat_lng.get('longitude')
    request_id = data.get('request_id', {})
    
    # For a real implementation, we would use the request_id to retrieve the 
    # saved state and calculate the precise path to this point
    
    # Find the nearest stop to get some real route info
    nearby_stops = find_nearest_stops(lat, lng, max_distance=2000)
    if not nearby_stops:
        # Fallback dummy path
        path = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-81.2497, 42.9849],  # Approximate center of London
                    [lng, lat]
                ]
            },
            "properties": {
                "color": "#ff0000",
                "line_width": 4
            }
        }
        
        detail_items = [{
            "type": "walking",
            "distance": 250,
            "duration": 300,
            "from_name": "Origin",
            "to_name": "Bus Stop",
            "elevation_gain": 0,
            "elevation_loss": 0
        }, {
            "type": "transit",
            "route_name": "2 Dundas",
            "route_short_name": "2",
            "trip_headsign": "Downtown",
            "from_name": "Bus Stop",
            "to_name": "Destination",
            "start_time": "08:15:00",
            "end_time": "08:25:00",
            "agency_name": "London Transit",
            "duration": 600,
            "route_color": "#0000ff"
        }]
    else:
        nearest_stop = nearby_stops[0]
        
        # Get departures from this stop
        departures = get_next_departures(nearest_stop['stop_id'], 8 * 3600)
        
        if len(departures) > 0:
            departure = departures.iloc[0]
            route_id = departure['route_id']
            trip_id = departure['trip_id']
            route = gtfs_data['routes'][gtfs_data['routes'].route_id == route_id].iloc[0]
            
            # Get trip stops to show the path
            trip_stops = get_trip_stops(trip_id)
            
            # Create path coordinates
            coords = []
            for _, stop in trip_stops.iterrows():
                coords.append([stop.stop_lon, stop.stop_lat])
            
            # Add starting point
            coords.insert(0, [lng, lat])
            
            path = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "color": "#" + (route.route_color if hasattr(route, 'route_color') else "0000ff"),
                    "line_width": 4
                }
            }
            
            # Create transit details
            detail_items = [{
                "type": "walking",
                "distance": int(nearest_stop['distance']),
                "duration": int(nearest_stop['time_to_walk']),
                "from_name": "Origin",
                "to_name": nearest_stop['stop_name'],
                "elevation_gain": 0,
                "elevation_loss": 0
            }, {
                "type": "transit",
                "route_name": route.route_long_name if hasattr(route, 'route_long_name') else "Bus Route",
                "route_short_name": route.route_short_name,
                "trip_headsign": departure.trip_headsign if hasattr(departure, 'trip_headsign') else "London Transit",
                "from_name": nearest_stop['stop_name'],
                "to_name": trip_stops.iloc[-1].stop_name,
                "start_time": departure.departure_time,
                "end_time": trip_stops.iloc[-1].arrival_time,
                "agency_name": "London Transit",
                "duration": trip_stops.iloc[-1].arrival_secs - departure.departure_secs,
                "route_color": "#" + (route.route_color if hasattr(route, 'route_color') else "0000ff")
            }]
        else:
            # Fallback dummy path
            path = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-81.2497, 42.9849],
                        [lng, lat]
                    ]
                },
                "properties": {
                    "color": "#ff0000",
                    "line_width": 4
                }
            }
            
            detail_items = [{
                "type": "walking",
                "distance": 250,
                "duration": 300,
                "from_name": "Origin",
                "to_name": "Bus Stop",
                "elevation_gain": 0,
                "elevation_loss": 0
            }, {
                "type": "transit",
                "route_name": "2 Dundas",
                "route_short_name": "2",
                "trip_headsign": "Downtown",
                "from_name": "Bus Stop",
                "to_name": "Destination",
                "start_time": "08:15:00",
                "end_time": "08:25:00",
                "agency_name": "London Transit",
                "duration": 600,
                "route_color": "#0000ff"
            }]
    
    return jsonify({
        "path": path,
        "details": detail_items
    })

@app.route('/api/v2/mvt/all_cities/<z>/<x>/<y>.bin', methods=['GET'])
def mvt(z, x, y):
    """
    Serve MVT tiles for the isochrone map.
    In a real implementation, we would generate proper vector tiles.
    For this simplified version, we'll return a placeholder.
    """
    # Return a minimal valid MVT tile
    response = app.response_class(
        response=b'',  # Empty tile
        status=204,
        mimetype='application/x-protobuf'
    )
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3030) 