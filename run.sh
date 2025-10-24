#!/bin/bash

# Root script to start Azurite and both Azure Functions apps

# Track background PIDs
AZURITE_PID=""
INGESTOR_PID=""
REFRESHER_PID=""

# Cleanup Azurite data from previous startup
rm -rf ./azurite/*

# Start Azurite (Blob, Queue, Table)
echo "Starting Azurite services..."
azurite --location ./azurite --silent &
AZURITE_PID=$!
sleep 2  # Give Azurite time to initialize

# Start traffic_ingestor
echo "Starting traffic_ingestor..."
(cd traffic_ingestor && func start) &
INGESTOR_PID=$!
sleep 2  # Optional: wait for ingestor to stabilize

# Start traffic_refresher on port 7072
echo "Starting traffic_refresher on port 7072..."
(cd traffic_refresher && func start --port 7072) &
REFRESHER_PID=$!

# Handle shutdown
cleanup() {
  echo ""
  echo "Shutting down all services..."
  kill $REFRESHER_PID 2>/dev/null
  kill $INGESTOR_PID 2>/dev/null
  kill $AZURITE_PID 2>/dev/null
  wait
  echo "All services stopped."
  exit 0
}

# Trap Ctrl+C or termination
trap cleanup SIGINT SIGTERM

# Keep script alive
echo "All services running. Press Ctrl+C to stop."
wait
