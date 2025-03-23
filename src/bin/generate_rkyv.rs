use timetoreach_lib::agencies::City;
use timetoreach_lib::gtfs_setup::initialize_gtfs_as_bson;

fn main() {
    println!("Generating .rkyv file for London");
    let _gtfs = initialize_gtfs_as_bson("city-gtfs/london", City::London);
    println!("Done generating .rkyv file for London");
}

