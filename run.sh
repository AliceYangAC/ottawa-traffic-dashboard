#!/bin/bash

# Ports to free
ports=(7071 7072 8000 8050)

echo "Checking and freeing ports..."
for port in "${ports[@]}"; do
    pids=$(netstat -anp 2>/dev/null | grep ":$port " | grep LISTEN | awk '{print $7}' | cut -d'/' -f1 | sort -u)

    for pid in $pids; do
        kill -9 $pid && echo "Force-killed PID $pid on port $port"
    done
done

# Clean Azurite data
echo "Cleaning Azurite data..."
mkdir -p ./azurite
rm -rf ./azurite/*

# Start Azurite
echo "Starting Azurite..."
azurite --location ./azurite --silent &
azurite_pid=$!
sleep 5

# Start traffic_ingester
echo "Starting traffic_ingester on port 7071..."
(cd traffic_ingester && func start --port 7071) &
ingester_pid=$!
sleep 10

# Start Dash dashboard
echo "Starting Dash dashboard on port 8050..."
(python -m dashboard.app) &
dashboard_pid=$!
sleep 2

# Trap Ctrl+C and clean up
cleanup() {
    echo ""
    echo "Shutting down all services..."
    kill -9 $dashboard_pid $websocket_pid $refresher_pid $ingester_pid $azurite_pid 2>/dev/null

    echo "Cleaning up lingering ports..."
    for port in "${ports[@]}"; do
        pids=$(netstat -anp 2>/dev/null | grep ":$port " | grep LISTEN | awk '{print $7}' | cut -d'/' -f1 | sort -u)
        for pid in $pids; do
            kill -9 $pid && echo "Force-killed lingering PID $pid on port $port"
        done
    done

    echo "All services and ports cleaned up."
    exit 0
}

trap cleanup SIGINT

echo ""
echo "All services running. Press Ctrl+C to stop."
echo ""
echo "To start fetching traffic events, run:"
echo "  curl http://localhost:7071/api/FetchTrafficEvents"

# Keep script alive
while true; do
    sleep 1
done
