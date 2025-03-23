import json
import math
import os
import random

# London, Ontario transit locations
ORIGIN_LAT = 43.00754265588104
ORIGIN_LNG = -81.2764633569997

# Define some key bus stations and stops in London, Ontario
BUS_STOPS = [
    {"name": "Downtown Terminal", "lat": 42.9837, "lng": -81.2497, "time": 0},
    {"name": "Fanshawe College", "lat": 43.0127, "lng": -81.1996, "time": 20},
    {"name": "Western University", "lat": 43.0096, "lng": -81.2737, "time": 10},
    {"name": "White Oaks Mall", "lat": 42.9255, "lng": -81.2284, "time": 25},
    {"name": "Masonville Place", "lat": 43.0306, "lng": -81.2752, "time": 15},
    {"name": "Victoria Hospital", "lat": 42.9639, "lng": -81.2230, "time": 18},
    {"name": "Westmount Mall", "lat": 42.9556, "lng": -81.2969, "time": 22},
    {"name": "Argyle Mall", "lat": 42.9845, "lng": -81.1944, "time": 30},
    {"name": "Hyde Park", "lat": 43.0169, "lng": -81.3309, "time": 35},
    {"name": "Commissioners & Wellington", "lat": 42.9918, "lng": -81.2370, "time": 12},
    {"name": "London Health Sciences Centre", "lat": 43.0125, "lng": -81.2765, "time": 8},
    {"name": "Dundas & Richmond", "lat": 42.9854, "lng": -81.2530, "time": 5},
]

# Main bus routes that connect to our origin
BUS_ROUTES = [
    {
        "name": "Route 2 - Dundas",
        "color": "#FF0000", 
        "stops": [
            {"lat": 43.0075, "lng": -81.2765},  # Origin (approximate)
            {"lat": 43.0070, "lng": -81.2700},
            {"lat": 43.0060, "lng": -81.2600},
            {"lat": 43.0000, "lng": -81.2550},
            {"lat": 42.9854, "lng": -81.2530},  # Dundas & Richmond
            {"lat": 42.9837, "lng": -81.2497},  # Downtown Terminal
        ]
    },
    {
        "name": "Route 6 - Richmond",
        "color": "#0000FF",
        "stops": [
            {"lat": 43.0075, "lng": -81.2765},  # Origin (approximate)
            {"lat": 43.0100, "lng": -81.2760},
            {"lat": 43.0125, "lng": -81.2765},  # London Health Sciences Centre
            {"lat": 43.0200, "lng": -81.2770},
            {"lat": 43.0306, "lng": -81.2752},  # Masonville Place
        ]
    },
    {
        "name": "Route 9 - Whitehills",
        "color": "#00AA00",
        "stops": [
            {"lat": 43.0075, "lng": -81.2765},  # Origin (approximate)
            {"lat": 43.0050, "lng": -81.2800},
            {"lat": 43.0025, "lng": -81.2850},
            {"lat": 43.0000, "lng": -81.2900},
            {"lat": 42.9950, "lng": -81.2950},
            {"lat": 42.9556, "lng": -81.2969},  # Westmount Mall
        ]
    },
    {
        "name": "Route 13 - Wellington",
        "color": "#AA00AA",
        "stops": [
            {"lat": 43.0075, "lng": -81.2765},  # Origin (approximate)
            {"lat": 43.0050, "lng": -81.2700},
            {"lat": 43.0000, "lng": -81.2650},
            {"lat": 42.9950, "lng": -81.2600},
            {"lat": 42.9918, "lng": -81.2370},  # Commissioners & Wellington
            {"lat": 42.9837, "lng": -81.2497},  # Downtown Terminal
        ]
    }
]

# Define some additional points along routes for better interpolation
def generate_route_points():
    points = []
    
    # Add all bus stops
    for stop in BUS_STOPS:
        points.append({
            "lat": stop["lat"],
            "lng": stop["lng"],
            "time": stop["time"],
            "name": stop.get("name", "Bus Stop")
        })
    
    # Add points along routes
    for route in BUS_ROUTES:
        stops = route["stops"]
        for i in range(len(stops) - 1):
            # Add intermediate points between each pair of stops
            start = stops[i]
            end = stops[i+1]
            
            # Calculate approximate time between stops based on distance
            lat_diff = end["lat"] - start["lat"]
            lng_diff = end["lng"] - start["lng"]
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111  # km
            time_minutes = (distance / 20) * 60  # Assuming 20 km/h
            
            # Add 2 intermediate points
            for j in range(1, 3):
                fraction = j / 3
                new_lat = start["lat"] + lat_diff * fraction
                new_lng = start["lng"] + lng_diff * fraction
                
                # Calculate time (adjusted by fraction of distance)
                # Find closest actual stop to start to get a baseline time
                start_time = 0
                for stop in BUS_STOPS:
                    if abs(stop["lat"] - start["lat"]) < 0.001 and abs(stop["lng"] - start["lng"]) < 0.001:
                        start_time = stop["time"]
                        break
                
                # If we couldn't find a matching stop, use origin
                if start_time == 0:
                    # Calculate from origin
                    orig_lat_diff = start["lat"] - ORIGIN_LAT
                    orig_lng_diff = start["lng"] - ORIGIN_LNG
                    orig_distance = math.sqrt(orig_lat_diff**2 + orig_lng_diff**2) * 111
                    start_time = (orig_distance / 20) * 60
                
                # Time at this intermediate point
                point_time = start_time + time_minutes * fraction
                
                points.append({
                    "lat": new_lat,
                    "lng": new_lng,
                    "time": round(point_time),
                    "name": f"Along {route['name']}"
                })
    
    return points

# Generate additional points to create a grid
def generate_grid_points():
    # Define bounds of London, Ontario
    min_lat = 42.90
    max_lat = 43.10
    min_lng = -81.40
    max_lng = -81.10
    
    # Create a grid of points
    grid_points = []
    lat_step = 0.01  # About 1km
    lng_step = 0.01
    
    for lat in [min_lat + i * lat_step for i in range(int((max_lat - min_lat) / lat_step) + 1)]:
        for lng in [min_lng + i * lng_step for i in range(int((max_lng - min_lng) / lng_step) + 1)]:
            # Skip points too far from London's center (rough approximation)
            center_lat = 42.98
            center_lng = -81.25
            lat_diff = lat - center_lat
            lng_diff = lng - center_lng
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111  # km
            if distance > 15:  # London is roughly 15km across
                continue
                
            # Calculate time based on distance and routes
            time = calculate_travel_time(lat, lng)
            
            if time <= 60:  # Only include points reachable within an hour
                grid_points.append({
                    "lat": lat,
                    "lng": lng,
                    "time": time,
                    "name": "Grid Point"
                })
    
    return grid_points

# Calculate travel time from origin to a point
def calculate_travel_time(lat, lng):
    # First check if this is a known bus stop
    for stop in BUS_STOPS:
        if abs(stop["lat"] - lat) < 0.001 and abs(stop["lng"] - lng) < 0.001:
            return stop["time"]
    
    # Check if this point is close to a bus route
    min_time = float('inf')
    
    for route in BUS_ROUTES:
        stops = route["stops"]
        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i+1]
            
            # Check if point is close to this line segment
            close, segment_fraction = point_to_segment_distance(
                lat, lng, 
                start["lat"], start["lng"], 
                end["lat"], end["lng"]
            )
            
            if close < 0.005:  # About 500m
                # This point is close to a bus route
                # Find time to start of segment
                start_time = 0
                for stop in BUS_STOPS:
                    if abs(stop["lat"] - start["lat"]) < 0.001 and abs(stop["lng"] - start["lng"]) < 0.001:
                        start_time = stop["time"]
                        break
                
                # If we couldn't find a matching stop, calculate from origin
                if start_time == 0:
                    orig_lat_diff = start["lat"] - ORIGIN_LAT
                    orig_lng_diff = start["lng"] - ORIGIN_LNG
                    orig_distance = math.sqrt(orig_lat_diff**2 + orig_lng_diff**2) * 111
                    start_time = (orig_distance / 20) * 60
                
                # Calculate time based on segment location
                lat_diff = end["lat"] - start["lat"]
                lng_diff = end["lng"] - start["lng"]
                segment_distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111
                segment_time = (segment_distance / 20) * 60
                
                point_time = start_time + segment_time * segment_fraction
                point_time += close * 111 / 0.07  # Walking time to route (4.2 km/h)
                
                min_time = min(min_time, point_time)
    
    # If no route is close, calculate direct time from origin
    if min_time == float('inf'):
        lat_diff = lat - ORIGIN_LAT
        lng_diff = lng - ORIGIN_LNG
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111
        direct_time = (distance / 20) * 60  # Bus at 20 km/h
        
        # Add some randomness to simulate real-world conditions
        direct_time += random.uniform(-5, 10)
        direct_time = max(5, direct_time)  # Minimum 5 minutes
        
        min_time = direct_time
    
    # Add some randomness to simulate real-world conditions
    min_time += random.uniform(-2, 5)
    min_time = max(5, min_time)  # Minimum 5 minutes
    
    return round(min_time)

# Calculate distance from point to line segment and fractional position
def point_to_segment_distance(px, py, x1, y1, x2, y2):
    line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if line_length == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2), 0
    
    # Calculate projection
    t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_length * line_length)
    t = max(0, min(1, t))
    
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    
    distance = math.sqrt((px - projection_x)**2 + (py - projection_y)**2)
    
    return distance, t

def create_contour_map():
    print("Generating isochrone contour map...")
    
    # Generate points
    route_points = generate_route_points()
    grid_points = generate_grid_points()
    all_points = route_points + grid_points
    
    print(f"Generated {len(all_points)} points for contour map")
    
    # Create time buckets
    time_buckets = {
        "0-15": {"color": "#00FF00", "opacity": 0.7, "points": []},
        "15-30": {"color": "#0000FF", "opacity": 0.6, "points": []},
        "30-45": {"color": "#FF00FF", "opacity": 0.5, "points": []},
        "45-60": {"color": "#FF0000", "opacity": 0.4, "points": []}
    }
    
    # Sort points into buckets
    for point in all_points:
        time = point["time"]
        if time <= 15:
            time_buckets["0-15"]["points"].append(point)
        elif time <= 30:
            time_buckets["15-30"]["points"].append(point)
        elif time <= 45:
            time_buckets["30-45"]["points"].append(point)
        elif time <= 60:
            time_buckets["45-60"]["points"].append(point)
    
    # Create HTML content
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transit Isochrone Map from {ORIGIN_LAT}, {ORIGIN_LNG}</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ height: 100vh; width: 100%; }}
            .legend {{ padding: 6px 8px; background: white; background: rgba(255,255,255,0.8); box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; }}
            .legend div {{ line-height: 18px; color: #555; }}
            .legend i {{ width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; }}
            .info {{ padding: 6px 8px; font: 14px/16px Arial, Helvetica, sans-serif; background: white; background: rgba(255,255,255,0.8); box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Initialize map
            var map = L.map('map').setView([{ORIGIN_LAT}, {ORIGIN_LNG}], 12);
            
            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
            }}).addTo(map);
            
            // Add marker for origin
            L.marker([{ORIGIN_LAT}, {ORIGIN_LNG}])
                .bindPopup("<b>Origin</b><br>Your starting point")
                .addTo(map);
            
            // Create contours (60 to 15 minutes, so outer rings are drawn first)
            var timeBuckets = {json.dumps(time_buckets)};
            var layerGroups = {{}};
            
            // Create contour polygons
            var timeRanges = Object.keys(timeBuckets).reverse();
            timeRanges.forEach(function(range) {{
                var bucket = timeBuckets[range];
                layerGroups[range] = L.layerGroup().addTo(map);
                
                // Create heatmap for this range
                var heatData = [];
                bucket.points.forEach(function(point) {{
                    heatData.push([point.lat, point.lng, 1]); // Weight of 1 for all points
                }});
                
                if (heatData.length > 0) {{
                    // Make the contour polygon by creating a circle for each point
                    bucket.points.forEach(function(point) {{
                        // Add a transparent circle for each point to create a contour-like effect
                        var radius = 300; // meters
                        L.circle([point.lat, point.lng], {{
                            radius: radius,
                            color: bucket.color,
                            weight: 1,
                            fillColor: bucket.color,
                            fillOpacity: 0.1,
                            opacity: 0.3
                        }}).addTo(layerGroups[range]);
                    }});
                    
                    // Add a heat layer for a smoother look
                    L.heatLayer(heatData, {{
                        radius: 25,
                        blur: 15,
                        maxZoom: 17,
                        max: 1.0,
                        gradient: {{0.4: bucket.color}}
                    }}).addTo(layerGroups[range]);
                }}
            }});
            
            // Add known bus stops
            var busStops = {json.dumps(BUS_STOPS)};
            busStops.forEach(function(stop) {{
                // Determine color based on time
                var color;
                if (stop.time <= 15) {{
                    color = "#00FF00";
                }} else if (stop.time <= 30) {{
                    color = "#0000FF";
                }} else if (stop.time <= 45) {{
                    color = "#FF00FF";
                }} else {{
                    color = "#FF0000";
                }}
                
                L.circleMarker([stop.lat, stop.lng], {{
                    radius: 6,
                    fillColor: color,
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }})
                .bindPopup("<b>" + stop.name + "</b><br>Travel time: " + stop.time + " minutes")
                .addTo(map);
            }});
            
            // Add bus routes
            var busRoutes = {json.dumps(BUS_ROUTES)};
            
            busRoutes.forEach(function(route) {{
                var points = route.stops.map(function(stop) {{
                    return [stop.lat, stop.lng];
                }});
                
                L.polyline(points, {{
                    color: route.color,
                    weight: 5,
                    opacity: 0.7
                }})
                .bindPopup("<b>" + route.name + "</b>")
                .addTo(map);
            }});
            
            // Add legend
            var legend = L.control({{position: 'bottomright'}});
            
            legend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML += '<h4>Travel Time</h4>';
                div.innerHTML += '<div><i style="background: #00FF00"></i> 0-15 minutes</div>';
                div.innerHTML += '<div><i style="background: #0000FF"></i> 15-30 minutes</div>';
                div.innerHTML += '<div><i style="background: #FF00FF"></i> 30-45 minutes</div>';
                div.innerHTML += '<div><i style="background: #FF0000"></i> 45-60 minutes</div>';
                div.innerHTML += '<h4>Bus Routes</h4>';
                
                busRoutes.forEach(function(route) {{
                    div.innerHTML += '<div><i style="background: ' + route.color + '"></i> ' + route.name + '</div>';
                }});
                
                return div;
            }};
            
            legend.addTo(map);
            
            // Add info box
            var info = L.control({{position: 'topleft'}});
            
            info.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'info');
                div.innerHTML = '<h4>London Transit Isochrone Map</h4>' +
                                '<p>This map shows estimated travel times from the marked origin point using London Transit.</p>' +
                                '<p>Data is approximated and for visualization purposes only.</p>';
                return div;
            }};
            
            info.addTo(map);
        </script>
    </body>
    </html>
    """
    
    # Write to file
    filename = f"isochrone_contour_{ORIGIN_LAT}_{ORIGIN_LNG}.html"
    with open(filename, "w") as f:
        f.write(html)
    
    print(f"Contour map created: {filename}")
    return filename

if __name__ == "__main__":
    map_file = create_contour_map()
    
    # Try to open the file automatically
    try:
        import webbrowser
        print(f"Opening {map_file} in your default browser...")
        webbrowser.open('file://' + os.path.realpath(map_file))
    except:
        print(f"Please open {map_file} in your browser to view the map.") 