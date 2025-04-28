#!/bin/bash

# Kill any running Django servers
echo "Stopping any running Django servers..."
pkill -f "python manage.py runserver" || echo "No running servers found"

# Wait a moment
sleep 1

# Start the server in the background
echo "Starting Django server..."
python manage.py runserver &

# Wait for server to start
sleep 2

echo "Server is running. Access the API at http://localhost:8000/api/"
echo "Access the API Key Setup page at http://localhost:8000/static/apikey_setup.html" 