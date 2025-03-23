use petgraph::visit::EdgeCount;
use serde_json::json;
use std::sync::RwLock;
use crate::gtfs::{Stop, SpatialStopsWithTrips};
use crate::web_app_data::RequestId;
    lat: f64,
    lng: f64,
    include_agencies: Vec<String>,
    include_modes: Vec<String>,
    start_time: u64,
    max_search_time: f64,
    transfer_cost_secs: u64,
) -> Result<Json, BadQuery> {
    log::debug!("Processing coordinates for lat={}, lng={}", lat, lng);
    let city = check_city(&ad, lat, lng);

    if city.is_none() {
        log::warn!("No city found for coordinates: lat={}, lng={}", lat, lng);
        return Err(BadQuery::from("Invalid city"));
    }

    let city = city.unwrap();
    log::info!("Processing request for city: {:?}", city);
    let ad = ad.ads.get(&city).unwrap();
    let gtfs = &ad.gtfs;
    let spatial_stops = &ad.spatial;

    // Validate that GTFS data contains routes
    if gtfs.routes.is_empty() {
        log::error!("No routes found in GTFS data for city: {:?}", city);
        return Err(BadQuery::from("No routes available for this city"));
    }
    
    // Get agency IDs for the city
    let agency_ids: Vec<String> = if include_agencies.is_empty() {
        gtfs.agencies.keys().cloned().collect()
    } else {
        include_agencies
    };

    if agency_ids.is_empty() {
        log::warn!("No agencies selected for processing in city: {:?}", city);
        return Err(BadQuery::from("No valid agencies selected"));
    }
    log::debug!("Final agency_ids being processed: {:?}", agency_ids);

    // Convert modes to route types
    let modes = include_modes;
    
    // Log stop search process
    let coord = gtfs_structure::Coord {
        lat,
        lon: lng,
    };

    let nearest_stops: Vec<_> = gtfs.stops.iter()
        .map(|(stop_id, stop)| {
            let dist = coord.distance_to(&stop.coord);
            (stop_id, stop, dist)
        })
        .filter(|(_, _, dist)| *dist <= 1000.0) // 1km radius
        .collect();

    log::info!(
        "Found {} stops within 1km of coordinates ({}, {})",
        nearest_stops.len(),
        lat,
        lng
    );

    if !nearest_stops.is_empty() {
        log::info!("Nearest stops:");
        for (stop_id, stop, dist) in nearest_stops.iter().take(5) {
            log::info!(
                "  - {} (ID: {}): {:.2}m away at ({}, {})",
                stop.name,
                stop_id,
                dist,
                stop.coord.lat,
                stop.coord.lon
            );
        }
    }

    // Also log the modes we're using
    log::info!("Searching for route types: {:?}", modes);
    
    // Convert start_time to a human-readable format for logging
    let hours = (start_time / 3600) % 24;
    let minutes = (start_time % 3600) / 60;
    let seconds = start_time % 60;

    log::info!(
        "Processing reach times for time {:02}:{:02}:{:02} with max search time {} seconds",
        hours,
        minutes,
        seconds,
        max_search_time
    );

    // Add service period validation
    let test_date = chrono::NaiveDate::from_ymd_opt(2025, 2, 5).unwrap(); // A Wednesday in the valid range
    let current_services = gtfs.get_service_ids_for_date(&test_date);
    log::info!("Available service IDs for test date {}: {:?}", test_date, current_services);

    // Log route information
    let route_count = gtfs.routes.len();
    let active_routes = gtfs.routes.iter()
        .filter(|(_, route)| modes.contains(&route.route_type.to_string()))
        .count();

    log::info!(
        "Found {}/{} routes matching requested modes: {:?}",
        active_routes,
        route_count,
        modes
    );

    // Add trip validation
    let trip_count = gtfs.trips.len();
    let active_trips = gtfs.trips.iter()
        .filter(|(_, trip)| {
            if let Some(route) = gtfs.routes.get(&trip.route_id) {
                modes.contains(&route.route_type.to_string())
            } else {
                false
            }
        })
        .count();

    log::info!(
        "Found {}/{} trips for matching routes",
        active_trips,
        trip_count
    );

    let mut rs = ad.rs_template.clone();

    // Generate reach times and capture any errors
    let result = time_to_reach::generate_reach_times(
        gtfs,
        spatial_stops,
        &mut rs,
        Configuration {
            start_time: Time(start_time as f64),
            duration_secs: max_search_time,
            location: LatLng {
                latitude: lat,
                longitude: lng,
            },
            agency_ids,
            transfer_cost: transfer_cost_secs,
            modes,
        },
    );

    match result {
        Ok(edge_times) => {
            log::info!("Successfully generated {} edge times", edge_times.len());
            Ok(Json(edge_times))
        },
        Err(e) => {
            log::error!("Error generating reach times: {:?}", e);
            Err(BadQuery::from(e))
        }
    }
