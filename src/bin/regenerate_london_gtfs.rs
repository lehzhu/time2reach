use std::fs;
use crate::agencies::City;
use crate::gtfs_setup::initialize_gtfs_as_bson;

fn main() {
    println!("Regenerating London GTFS data");
    
    // Delete the existing .rkyv file to force regeneration
    let rkyv_path = "city-gtfs/london-1.rkyv";
    if let Ok(_) = fs::remove_file(rkyv_path) {
        println!("Deleted existing file: {}", rkyv_path);
    }
    
    // Initialize the GTFS data
    println!("Initializing London GTFS data...");
    let gtfs_list = initialize_gtfs_as_bson("city-gtfs/london", City::London);
    
    // Print statistics
    println!("GTFS data regenerated with {} agencies", gtfs_list.len());
    for (i, gtfs) in gtfs_list.iter().enumerate() {
        println!("Agency #{}: {}", i + 1, gtfs.agency_name);
        println!("  Routes: {}", gtfs.routes.len());
        println!("  Trips: {}", gtfs.trips.len());
        println!("  Stops: {}", gtfs.stops.len());
    }
    
    println!("\nLondon GTFS data has been regenerated successfully!");
} 