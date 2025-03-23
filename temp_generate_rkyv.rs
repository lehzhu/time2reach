use std::env;
use crate::agencies::City;
use crate::gtfs_setup::initialize_gtfs_as_bson;

pub fn main() {
    println!("Generating .rkyv file for London");
    let _gtfs = initialize_gtfs_as_bson("city-gtfs/london", City::London);
    println!("Done generating .rkyv file for London");
}

