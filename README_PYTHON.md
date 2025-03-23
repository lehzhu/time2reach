# Simplified Transit Isochrone Map for London, Ontario

This is a simplified Python backend for generating transit isochrone maps for London, Ontario bus routes. It is designed to work with the existing Vite/React frontend with minimal modifications.

## Features

- Focus on London, Ontario transit data only
- Bus routes only (no other modes of transportation)
- Simplified isochrone calculation
- Python-based for easier maintenance and extension
- Same API endpoints as the original Rust backend

## Requirements

- Python 3.9+
- Pip packages in requirements.txt

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the preprocessing script: `python setup.py`
4. Start the server: `python app.py`

## Docker

You can also run the backend in a Docker container:

```bash
docker build -t transit-backend-python -f Dockerfile.python .
docker run -p 3030:3030 transit-backend-python
```

## API Endpoints

### Calculate Isochrone

```
POST /api/v2/hello/
```

Request body:
```json
{
  "latitude": 42.9849,
  "longitude": -81.2497,
  "startTime": 28800,
  "maxSearchTime": 3600,
  "agencies": ["LTC"],
  "modes": ["bus"],
  "transferPenaltySecs": 60
}
```

Response:
```json
{
  "request_id": {
    "rs_list_index": 1680123456,
    "city": "London"
  },
  "edge_times": {
    "s123": 120,
    "t456_789": 360
  }
}
```

### Get Trip Details

```
POST /api/v2/details/
```

Request body:
```json
{
  "request_id": {
    "rs_list_index": 1680123456,
    "city": "London"
  },
  "latlng": {
    "latitude": 42.9849,
    "longitude": -81.2497
  }
}
```

Response:
```json
{
  "path": {
    "type": "Feature",
    "geometry": {
      "type": "LineString",
      "coordinates": [
        [-81.2497, 42.9849],
        [-81.2498, 42.9850]
      ]
    },
    "properties": {
      "color": "#ff0000",
      "line_width": 4
    }
  },
  "details": [
    {
      "type": "walking",
      "distance": 250,
      "duration": 300,
      "from_name": "Origin",
      "to_name": "Bus Stop",
      "elevation_gain": 0,
      "elevation_loss": 0
    },
    {
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
    }
  ]
}
```

## Implementation Details

This simplified backend:

1. Uses the Partridge library to parse GTFS data
2. Builds a spatial index for efficient nearest-stop searches
3. Implements a simplified isochrone calculation algorithm
4. Provides the same API endpoints as the original Rust backend
5. Focuses only on London, Ontario bus routes

## Performance Considerations

- The preprocessed data is cached for faster startup
- Spatial indexing is used for efficient nearest-stop searches
- Time values are pre-calculated in seconds for faster comparison

## Limitations

- Only supports London, Ontario
- Only supports bus routes
- Does not generate actual MVT tiles (returns empty tiles)
- May not handle very large isochrones as efficiently as the Rust backend 