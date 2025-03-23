use serde_json::json;
use std::process::Command;

fn main() {
    println!("Testing London API fix...");
    
    // The problematic coordinate that was failing
    let test_coordinate = json!({
        "latitude": 43.00335993382387,
        "longitude": -81.23856030844863,
        "agencies": [],
        "modes": ["bus", "subway", "tram", "rail", "ferry"],
        "startTime": 63600,
        "maxSearchTime": 2700,
        "transferPenaltySecs": 0,
        "previousRequestId": null
    });
    
    println!("\nSending test request to the local API...");
    println!("Request payload: {}", test_coordinate.to_string());
    
    // Save the test payload to a temporary file
    std::fs::write("/tmp/london_test_payload.json", test_coordinate.to_string())
        .expect("Failed to write test payload");
    
    // Execute curl command to test the API
    let output = Command::new("curl")
        .args(&[
            "-s",
            "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", "@/tmp/london_test_payload.json",
            "http://localhost:3030/hello/"
        ])
        .output()
        .expect("Failed to execute curl");
    
    let response = String::from_utf8_lossy(&output.stdout);
    println!("\nResponse raw (first 500 chars):");
    if response.len() > 500 {
        println!("{}", &response[..500]);
        println!("... (truncated)");
    } else {
        println!("{}", response);
    }
    
    // Check if we got a response at all
    if response.trim().is_empty() {
        println!("\nERROR: Empty response - Is the server running at localhost:3030?");
        
        // Check curl exit code
        if !output.status.success() {
            println!("Curl error: {}", output.status);
            println!("Stderr: {}", String::from_utf8_lossy(&output.stderr));
        }
        return;
    }
    
    // Parse the response to check if it has edge_times
    match serde_json::from_str::<serde_json::Value>(&response) {
        Ok(response_json) => {
            if let Some(edge_times) = response_json.get("edge_times") {
                if let Some(obj) = edge_times.as_object() {
                    println!("\nSuccess! Response contains {} edge_times entries", obj.len());
                } else {
                    println!("\nWarning: edge_times is not an object");
                }
            } else {
                println!("\nWarning: Response is missing edge_times");
            }
            
            if let Some(request_id) = response_json.get("request_id") {
                println!("Request ID: {}", request_id);
            }
        }
        Err(e) => {
            println!("\nFailed to parse response as JSON: {}", e);
            println!("First 20 bytes: {:?}", response.as_bytes().iter().take(20).collect::<Vec<_>>());
            
            // Try to read the first valid JSON character to see where it breaks
            let chars: Vec<char> = response.chars().collect();
            let mut first_json_char = None;
            for (i, c) in chars.iter().enumerate() {
                if *c == '{' || *c == '[' {
                    first_json_char = Some((i, *c));
                    break;
                }
            }
            
            if let Some((idx, c)) = first_json_char {
                println!("First JSON character '{}' found at position {}", c, idx);
                if idx > 0 {
                    println!("Content before first JSON char: {:?}", &response[..idx]);
                }
            } else {
                println!("No valid JSON start character found in the response");
            }
        }
    }
} 