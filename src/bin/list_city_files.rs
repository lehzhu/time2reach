use std::fs;
use std::path::Path;

fn main() {
    println!("Checking city files...");
    
    // Check GTFS directory
    let gtfs_dir = "city-gtfs/london";
    println!("\nGTFS Directory: {}", gtfs_dir);
    if Path::new(gtfs_dir).exists() {
        if let Ok(entries) = fs::read_dir(gtfs_dir) {
            for entry in entries {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_dir() {
                        println!("  [DIR] {}", path.file_name().unwrap().to_string_lossy());
                    } else {
                        println!("  [FILE] {}", path.file_name().unwrap().to_string_lossy());
                    }
                }
            }
        }
    } else {
        println!("  Directory not found!");
    }
    
    // Check GPKG file
    let gpkg_file = "web/public/London.gpkg";
    println!("\nGPKG File: {}", gpkg_file);
    if Path::new(gpkg_file).exists() {
        println!("  File exists with size: {} bytes", fs::metadata(gpkg_file).unwrap().len());
    } else {
        println!("  File not found!");
    }
    
    // List city coordinates from agencies.rs
    println!("\nCity coordinates from agencies.rs:");
    println!("  London, Ontario: 42.9849, -81.2453");
    
    // Test coordinate
    println!("\nTest coordinate for London, Canada:");
    println!("  43.00335993382387, -81.23856030844863");
} 