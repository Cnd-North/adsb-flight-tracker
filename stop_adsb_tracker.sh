#!/bin/bash

# ADS-B Flight Tracker - Master Stop Script
# Stops all components gracefully

echo "============================================================"
echo "  ADS-B Flight Tracker - Stopping All Services"
echo "============================================================"
echo ""

# Colors for status
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to stop a process
stop_process() {
    local pattern="$1"
    local name="$2"

    echo -n "Stopping $name... "

    pkill -f "$pattern"
    sleep 1

    if ! pgrep -f "$pattern" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ (still running)${NC}"
    fi
}

# Stop all services in reverse order
stop_process "python.*http.server.*8080" "Web Server"
stop_process "signal_logger.py" "Signal Logger"
stop_process "position_tracker.py" "Position Tracker"
stop_process "log_server.py" "Log API Server"
stop_process "flight_logger_enhanced.py" "Flight Logger"
stop_process "dump1090.*--net" "dump1090"

echo ""
echo "============================================================"
echo "  All services stopped"
echo "============================================================"
echo ""
echo "To restart: ./start_adsb_tracker.sh"
echo ""
