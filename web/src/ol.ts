// import mapboxgl from "mapbox-gl";
//
// import { get_details } from "./get_data";
// import { TimeColorMapper } from "./colors";
//
// import { format_popup_html, TripDetailsTransit } from "./format-details";
// import settings_form_setup from "./settings-form";
// import setLoading from "./loading-spinner";
// import { getData, setData } from "./data-promise";
//
import { getData, setData } from "./data-promise";
import { TimeColorMapper } from "./colors";
import mapboxgl from "mapbox-gl";
import setLoading from "./loading-spinner";

export const startingLocation = new mapboxgl.LngLat(
    -73.99097283138498,
    40.743697683057555,
    // -79.61142287490227,
    // 43.68355164972115
);

export const CITY = "NewYorkCity"

export const defaultColor = "rgba(182,182,182,0.14)";


//
// settings_form_setup();
//
// map.on("load", async () => {
//     map.addSource("some id", {
//         type: "vector",
//         tiles: ["http://127.0.0.1:6767/edges/{z}/{x}/{y}.pbf"],
//     });
//
//     map.addLayer({
//         id: "transit-layer", // Layer ID
//         type: "line",
//         source: "some id", // ID of the tile source created above
//         "source-layer": "edges",
//         layout: {
//             "line-cap": "round",
//             "line-join": "round",
//         },
//         paint: {
//             "line-opacity": 0.3,
//             "line-color": default_color,
//             "line-width": 3.3,
//         },
//     });
//
//     await refetch_data(starting_location);
//
//     map.on("dblclick", async (e) => {
//         e.preventDefault();
//         await refetch_data(e.lngLat);
//     });
//
//     const popup = new mapboxgl.Popup({
//         maxWidth: "none",
//     });
//
//     let currentTask = undefined;
//     map.on("mouseover", "transit-layer", async (e) => {
//         const nearbyFeatures = map.queryRenderedFeatures(e.point);
//         if (nearbyFeatures.length === 0) return;
//
//         if (currentTask) clearTimeout(currentTask);
//
//         map.getCanvas().style.cursor = "crosshair";
//         currentTask = setTimeout(async () => {
//             const feature = nearbyFeatures[0];
//             popup.setLngLat(e.lngLat);
//             const seconds = getData().raw[feature.id];
//
//             if (!seconds) return;
//
//             const details: Array<TripDetailsTransit> = await get_details(
//                 getData(),
//                 {
//                     latitude: e.lngLat.lat,
//                     longitude: e.lngLat.lng,
//                 }
//             );
//
//             popup.setHTML(format_popup_html(seconds, details));
//             popup.addTo(map);
//         }, 400);
//     });
//     map.on("mouseleave", "transit-layer", () => {
//         map.getCanvas().style.cursor = "";
//         popup.remove();
//         clearTimeout(currentTask);
//         currentTask = undefined;
//     });
// });
