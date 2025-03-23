use crate::agencies::City;
use crate::gtfs_setup::initialize_gtfs_as_bson;
use std::fs::File;
use std::io::Read;
use crate::gtfs_processing::StopsWithTrips;

fn main() {
    // Load London GTFS data
    println!("Reading London GTFS data");
    
    // Try to read the existing .rkyv file
    let gtfs_path = "city-gtfs/london";
    let rkyv_path = format!("{}-1.rkyv", gtfs_path);
    
    if let Ok(mut file) = File::open(&rkyv_path) {
        println!("Found existing .rkyv file: {}", rkyv_path);
        
        // Read the file (just to check if it's valid)
        let mut bytes = Vec::new();
        match file.read_to_end(&mut bytes) {
            Ok(_) => println!("Successfully read {} bytes", bytes.len()),
            Err(e) => println!("Error reading file: {}", e),
        }
        
        // Now load the GTFS data properly using the same function as the server
        println!("\nLoading GTFS data using initialize_gtfs_as_bson");
        let gtfs_list = initialize_gtfs_as_bson(gtfs_path, City::London);
        
        // Print some statistics about the data
        println!("\nGTFS Statistics:");
        for (i, gtfs) in gtfs_list.iter().enumerate() {
            println!("Agency #{}: {}", i + 1, gtfs.agency_name);
            println!("  City: {}", gtfs.agency_city);
            println!("  Routes: {}", gtfs.routes.len());
            println!("  Trips: {}", gtfs.trips.len());
            println!("  Stops: {}", gtfs.stops.len());
            println!("  Shapes: {}", gtfs.shapes.len());
            println!("  Generated shapes: {}", gtfs.generated_shapes.len());

            // Create stops with trips to check if they can be processed
            let stops_with_trips = crate::gtfs_setup::generate_stops_trips(gtfs);
            
            // Check the number of stops with scheduled trips
            println!("  Stops with trips: {}", stops_with_trips.0.len());
            
            // Sample a few stop IDs
            if !stops_with_trips.0.is_empty() {
                println!("\n  Sample stops with trips:");
                for (i, (stop_id, _)) in stops_with_trips.0.iter().take(5).enumerate() {
                    if let Some(stop) = gtfs.stops.get(stop_id) {
                        println!("    Stop #{}: ID={:?}, Name={}, Coords=({}, {})", 
                            i + 1, 
                            stop_id, 
                            stop.stop_name.as_ref().unwrap_or(&"<no name>".to_string()),
                            stop.latitude.unwrap_or(0.0),
                            stop.longitude.unwrap_or(0.0)
                        );
                    }
                }
            }
        }
    } else {
        println!("No .rkyv file found at: {}", rkyv_path);
        println!("Creating new .rkyv file...");
        let gtfs_list = initialize_gtfs_as_bson(gtfs_path, City::London);
        println!("Created {} agencies", gtfs_list.len());
    }
} 