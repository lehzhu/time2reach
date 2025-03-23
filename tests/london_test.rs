extern crate timetoreach;

use timetoreach::agencies::City;
use timetoreach::road_structure::RoadStructureInner;

#[test]
fn test_london_road_structure() {
    // Initialize the London road structure
    let road_structure = RoadStructureInner::new(City::London);
    
    // Print information about the road structure
    println!("London road structure loaded successfully!");
    println!("City: {:?}", City::London);
} 