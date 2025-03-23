#!/bin/bash

echo "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running preprocessing script..."
python setup.py

echo "Starting the backend server..."
python app.py 