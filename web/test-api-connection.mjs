import fetch from 'node-fetch';

async function testConnection() {
  console.log("Testing API endpoints...");
  
  try {
    const response = await fetch("https://map.henryn.ca/api/v2/hello/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        latitude: 42.9849,
        longitude: -81.2497,
        agencies: [],
        modes: ["bus", "subway", "tram", "rail", "ferry"],
        startTime: 61800,
        maxSearchTime: 2700,
        transferPenaltySecs: 0
      })
    });
    
    console.log("API Status:", response.status);
    if (response.ok) {
      console.log("API Response:", await response.json());
    } else {
      console.log("API Error:", await response.text());
    }
  } catch (error) {
    console.error("Connection Error:", error.message);
  }
  
  try {
    const mvtResponse = await fetch("https://map.henryn.ca/api/v2/mvt/london/10/10/10.bin");
    console.log("MVT Status:", mvtResponse.status);
    console.log("MVT Size:", mvtResponse.headers.get('content-length'));
  } catch (error) {
    console.error("MVT Connection Error:", error.message);
  }
}

testConnection();
