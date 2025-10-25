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
sleep 2

# Start traffic_ingestor
echo "Starting traffic_ingestor on port 7071..."
(cd traffic_ingestor && func start --port 7071) &
ingestor_pid=$!
# sleep 2

# Start traffic_refresher
echo "Starting traffic_refresher on port 7072..."
(cd traffic_refresher && func start --port 7072) &
refresher_pid=$!
# sleep 2

# Start WebSocket server
echo "Starting WebSocket server on port 8000..."
(cd websocket && python server.py) &
websocket_pid=$!
# sleep 2

# Start Dash dashboard
echo "Starting Dash dashboard on port 8050..."
(cd dashboard && python app.py) &
dashboard_pid=$!
# sleep 2

# Trap Ctrl+C and clean up
cleanup() {
    echo ""
    echo "Shutting down all services..."
    kill -9 $dashboard_pid $websocket_pid $refresher_pid $ingestor_pid $azurite_pid 2>/dev/null

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
