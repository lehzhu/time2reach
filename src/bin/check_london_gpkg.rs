use gdal::{Dataset, DatasetOptions, GdalOpenFlags};
use gdal::vector::LayerAccess;

fn main() {
    // Open the London GPKG file
    let options = DatasetOptions {
        open_flags: GdalOpenFlags::GDAL_OF_READONLY,
        allowed_drivers: None,
        open_options: None,
        sibling_files: None,
    };
    
    let gpkg_path = "web/public/London.gpkg";
    println!("Opening GPKG file: {}", gpkg_path);
    
    match Dataset::open_ex(gpkg_path, options) {
        Ok(dataset) => {
            // List all layers
            println!("GPKG Layers:");
            let layer_count = dataset.layer_count();
            for i in 0..layer_count {
                if let Ok(layer) = dataset.layer(i) {
                    let layer_name = layer.name();
                    let feature_count = layer.try_feature_count().unwrap_or(0);
                    println!("  - {}: {} features", layer_name, feature_count);
                }
            }
            
            // Check if nodes and edges exist
            if let Ok(mut edges_layer) = dataset.layer_by_name("edges") {
                println!("\nEdges layer exists with {} features", edges_layer.try_feature_count().unwrap_or(0));
            } else {
                println!("\nEdges layer not found!");
            }
            
            if let Ok(mut nodes_layer) = dataset.layer_by_name("nodes") {
                println!("Nodes layer exists with {} features", nodes_layer.try_feature_count().unwrap_or(0));
            } else {
                println!("Nodes layer not found!");
            }
        },
        Err(e) => {
            println!("Error opening GPKG file: {:?}", e);
        }
    }
} 