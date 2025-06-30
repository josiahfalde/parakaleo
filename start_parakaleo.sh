#!/bin/bash

# ParakaleoMed Clinic System Startup Script
# This script starts both the medical app and WebSocket server for real-time iPad synchronization

# Kill existing process on port 6789 (if any)
fuser -k 6789/tcp 2>/dev/null

echo "Starting ParakaleoMed Clinic System..."

# Set the working directory
cd /home/pi/parakaleo

# Start the WebSocket server in the background
echo "Starting WebSocket server for real-time iPad sync..."
python3 websocket_server.py &
WEBSOCKET_PID=$!

# Wait a moment for WebSocket server to initialize
sleep 3

# Start the main Streamlit application
echo "Starting ParakaleoMed medical application..."
/home/pi/parakaleo/venv/bin/streamlit run app.py --server.port 5000 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo "ParakaleoMed system started successfully!"
echo "WebSocket server running on port 6789 (PID: $WEBSOCKET_PID)"
echo "Medical app running on port 5000 (PID: $STREAMLIT_PID)"
echo "Access the clinic system at: http://192.168.4.1:5000"
echo "iPads will automatically sync in real-time"

# Keep the script running and monitor both processes
wait $STREAMLIT_PID
wait $WEBSOCKET_PID
