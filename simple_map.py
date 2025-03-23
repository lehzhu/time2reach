import json
import math
import os

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

# Calculate travel time from origin to each bus stop
def calculate_travel_times():
    for stop in BUS_STOPS:
        # If time is already set, use that
        if "time" in stop and stop["time"] > 0:
            continue
            
        # Calculate distance in km (very approximate)
        lat_diff = stop["lat"] - ORIGIN_LAT
        lng_diff = stop["lng"] - ORIGIN_LNG
        
        # Rough distance calculation
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111  # km
        
        # Assume average transit speed of 20 km/h
        time_minutes = (distance / 20) * 60
        
        # Add some randomness for realism
        import random
        time_minutes += random.randint(-5, 5)
        time_minutes = max(5, time_minutes)  # Minimum 5 minutes
        
        stop["time"] = round(time_minutes)

def create_html_map():
    # Generate isochrone data (15, 30, 45, 60 minute intervals)
    time_ranges = {
        "0-15": {"color": "#00FF00", "stops": []},  # Green
        "15-30": {"color": "#0000FF", "stops": []},  # Blue
        "30-45": {"color": "#FF00FF", "stops": []},  # Purple
        "45-60": {"color": "#FF0000", "stops": []}   # Red
    }
    
    # Categorize stops by travel time
    for stop in BUS_STOPS:
        time = stop["time"]
        if time <= 15:
            time_ranges["0-15"]["stops"].append(stop)
        elif time <= 30:
            time_ranges["15-30"]["stops"].append(stop)
        elif time <= 45:
            time_ranges["30-45"]["stops"].append(stop)
        elif time <= 60:
            time_ranges["45-60"]["stops"].append(stop)
    
    # Create HTML content
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transit Travel Time from {ORIGIN_LAT}, {ORIGIN_LNG}</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ height: 100vh; width: 100%; }}
            .legend {{ padding: 6px 8px; background: white; background: rgba(255,255,255,0.8); box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 5px; }}
            .legend div {{ line-height: 18px; color: #555; }}
            .legend i {{ width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; }}
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
            
            // Add time range circles
            var timeRanges = {json.dumps(time_ranges)};
            
            // Create feature groups for each time range
            var layers = {{}};
            
            // Add bus stops by time range
            Object.keys(timeRanges).forEach(function(range) {{
                layers[range] = L.featureGroup().addTo(map);
                
                timeRanges[range].stops.forEach(function(stop) {{
                    L.circleMarker([stop.lat, stop.lng], {{
                        radius: 6,
                        fillColor: timeRanges[range].color,
                        color: "#000",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    }})
                    .bindPopup("<b>" + stop.name + "</b><br>Travel time: " + stop.time + " minutes")
                    .addTo(layers[range]);
                }});
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
        </script>
    </body>
    </html>
    """
    
    # Write to file
    filename = f"isochrone_map_{ORIGIN_LAT}_{ORIGIN_LNG}.html"
    with open(filename, "w") as f:
        f.write(html)
    
    print(f"Map created: {filename}")
    return filename

if __name__ == "__main__":
    calculate_travel_times()
    map_file = create_html_map()
    
    # Try to open the file automatically
    try:
        import webbrowser
        print(f"Opening {map_file} in your default browser...")
        webbrowser.open('file://' + os.path.realpath(map_file))
    except:
        print(f"Please open {map_file} in your browser to view the map.") 