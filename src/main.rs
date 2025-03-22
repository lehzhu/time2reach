use anyhow::Result;
mod agencies;
mod best_times;
mod configuration;
mod formatter;
mod gtfs_processing;
mod gtfs_setup;
mod in_progress_trip;
mod path_usage;
mod projection;
mod reach_data;
mod road_structure;
mod serialization;
mod time;
mod time_to_reach;
mod trip_details;
mod trips_arena;
mod web;
mod web_app_data;
mod web_cache;

#[macro_use]
pub(crate) mod cache_function;
mod elevation_script;

use gtfs_structure_2::gtfs_wrapper::DirectionType;

use rustc_hash::FxHashSet;

use gtfs_structure_2::IdType;
use std::time::Instant;
use tokio::runtime;

use crate::road_structure::RoadStructure;
use crate::web::LatLng;
use configuration::Configuration;
use gtfs_structure_2::gtfs_wrapper::Gtfs1;

use crate::agencies::{Agency, City};
use crate::formatter::time_to_point;
use crate::gtfs_setup::get_agency_id_from_short_name;
use time::Time;
use trips_arena::TripsArena;

use rusqlite::Connection;

const WALKING_SPEED: f64 = 1.42;
const STRAIGHT_WALKING_SPEED: f64 = 1.25;
pub const MIN_TRANSFER_SECONDS: f64 = 35.0;
pub const TRANSIT_EXIT_PENALTY: f64 = 10.0;
const NULL_ID: (u16, u64) = (u16::MAX, u64::MAX);

#[derive(Debug, Ord, PartialOrd, Eq, PartialEq, Clone)]
pub struct BusPickupInfo {
    timestamp: Time,
    stop_sequence_no: u16,
    trip_id: IdType,
}

fn direction_to_bool(d: &DirectionType) -> bool {
    match d {
        DirectionType::Outbound => true,
        DirectionType::Inbound => false,
    }
}

fn main1() {
    let (gtfs, agency) = setup_gtfs();

    let agency_ids: FxHashSet<u16> = agency
        .iter()
        .map(|a| get_agency_id_from_short_name(&a.public_name).unwrap())
        .collect();
    let data = gtfs_setup::generate_stops_trips(&gtfs).into_spatial(&City::Paris, &gtfs);

    let mut rs = RoadStructure::new_city(City::Paris);
    let time = Instant::now();
    for _ in 0..20 {
        rs.clear_data();
        time_to_reach::generate_reach_times(
            &gtfs,
            &data,
            &mut rs,
            Configuration {
                // start_time: Time(3600.0 * 13.0),
                start_time: Time(3600.0 * 17.0 + 60.0 * 20.0),
                duration_secs: 3600.0 * 2.0,
                location: LatLng::from_lat_lng(48.860679403040606, 2.3423617371568994),
                agency_ids: agency_ids.clone(),
                modes: vec![],
                transfer_cost: 0
            },
        );
        let et = rs.save();
        println!(
            "Edge times: {:?} {:?} {:?} {}",
            et[0],
            et[1],
            et[2],
            et.len()
        );
        let _fmter = time_to_point(
            &rs,
            &rs.trips_arena,
            &gtfs,
            [48.836143932204806, 2.240355829094007],
            true,
        );
        println!("{}", _fmter.unwrap());
    }
    println!("Elapsed: {}", time.elapsed().as_secs_f32());
}

fn main() {
    env_logger::init();
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        use tokio::io::AsyncBufReadExt;
        use warp::Filter;
        
        // Create a simple route for API testing
        let cors = warp::cors()
            .allow_any_origin()
            .allow_headers(vec!["content-type"])
            .allow_methods(vec!["GET", "POST", "OPTIONS"]);
        
        let api_route = warp::path("api")
            .and(warp::path("test"))
            .and(warp::get())
            .map(|| {
                log::info!("API test endpoint called");
                warp::reply::json(&serde_json::json!({
                    "status": "ok",
                    "message": "API is working correctly"
                }))
            })
            .with(cors.clone());
            
        let mvt_route = warp::path("mvt")
            .and(warp::path::param())
            .and(warp::path::param())
            .and(warp::path::param())
            .map(|z: u32, x: u32, y: u32| {
                log::info!("MVT endpoint called: z={}, x={}, y={}", z, x, y);
                warp::reply::json(&serde_json::json!({
                    "status": "ok",
                    "tile": {
                        "z": z,
                        "x": x,
                        "y": y
                    }
                }))
            })
            .with(cors.clone());
        
        let details_route = warp::path("details")
            .and(warp::post())
            .and(warp::body::json())
            .map(|body: serde_json::Value| {
                log::info!("Details endpoint called with body: {:?}", body);
                warp::reply::json(&serde_json::json!({
                    "status": "ok",
                    "path": {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [-0.1276, 51.5072],
                                [-0.13, 51.51],
                                [-0.14, 51.52]
                            ]
                        },
                        "properties": {}
                    },
                    "details": [
                        {
                            "type": "transit",
                            "mode": "bus",
                            "line_name": "Test Bus",
                            "start_time": 3600,
                            "end_time": 4200,
                            "start_point": [-0.1276, 51.5072],
                            "end_point": [-0.14, 51.52]
                        }
                    ]
                }))
            })
            .with(cors.clone());
            
        // Combine all routes
        let routes = api_route.or(mvt_route).or(details_route);
        
        // Start the server
        println!("Starting server on http://127.0.0.1:3030");
        warp::serve(routes).run(([127, 0, 0, 1], 3030)).await;
    });
}

fn setup_gtfs() -> (Gtfs1, Vec<Agency>) {
    let mut result = agencies::load_all_gtfs();
    result.remove(&City::Paris).unwrap()
}
