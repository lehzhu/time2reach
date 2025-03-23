#!/bin/bash

# Create a backup of original files
mkdir -p city-gtfs/london/backup
cp city-gtfs/london/*.txt city-gtfs/london/backup/

# Function to clean a CSV file
clean_csv() {
    local file=$1
    # Preserve header
    head -n1 "$file" > "${file}.tmp"
    # Clean data rows: remove spaces around commas, ensure consistent time format
    tail -n+2 "$file" | sed 's/[[:space:]]*,[[:space:]]*/,/g' >> "${file}.tmp"
    mv "${file}.tmp" "$file"
}

# Clean each GTFS file
for file in city-gtfs/london/*.txt; do
    echo "Cleaning $file..."
    clean_csv "$file"
done

echo "GTFS data cleaning completed!"

