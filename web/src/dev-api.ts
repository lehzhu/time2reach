// Configuration for development API endpoints

// Force local API mode
export const IS_LOCAL = true;
console.log("IS_LOCAL", IS_LOCAL);
export const LOCAL_API = true;

// Point all API requests to localhost:3030
export const baseUrl = "http://localhost:3030";

// Use localhost:3030 for MVT (MapBox Vector Tiles) as well
export const mvtUrl = "http://localhost:3030/mvt";

// @ts-expect-error window
window.sa_metadata = { local: LOCAL_API };
