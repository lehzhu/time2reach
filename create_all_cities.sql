-- Create the all_cities table
CREATE TABLE IF NOT EXISTS all_cities (
    id INTEGER PRIMARY KEY,
    geom TEXT,
    city TEXT
);

-- Import London data from existing tables
INSERT INTO all_cities (id, geom, city)
SELECT 
    e.id,
    json_object(
        'type', 'LineString',
        'coordinates', json_array(
            json_array(nA.lon, nA.lat),
            json_array(nB.lon, nB.lat)
        )
    ),
    'London'
FROM edges e
JOIN nodes nA ON e.nodeA = nA.node_id
JOIN nodes nB ON e.nodeB = nB.node_id; 