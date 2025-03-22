import { baseUrl } from "./dev-api";
import type { TripDetailsTransit } from './format-details';
import type mapboxgl from "mapbox-gl";

export interface DetailResponse {
    details: TripDetailsTransit[];
    path: GeoJSON.Feature;
    status: string;
}

export async function getDetails(requestId: any, lngLat: mapboxgl.LngLat, signal: AbortSignal): Promise<DetailResponse> {
    // The data we're sending to our API
    const postData = {
        request_id: requestId,
        latlng: {
            latitude: lngLat.lat,
            longitude: lngLat.lng,
        }
    };

    console.log("Making details request:", postData);

    const response = await fetch(`${baseUrl}/details`, {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(postData),
        signal,
    });

    console.log("Got details response:", response.status);
    const data = await response.json();
    console.log("Details data:", data);
    
    return data;
}
