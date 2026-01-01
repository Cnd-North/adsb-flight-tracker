#!/bin/bash

# ADS-B Flight Tracker - Status Checker
# Shows real-time status of all services

echo "============================================================"
echo "  ADS-B Flight Tracker - Service Status"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# Colors for status
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to get uptime
get_uptime() {
    local pid=$(pgrep -f "$1" | head -1)
    if [ -n "$pid" ]; then
        ps -p "$pid" -o etime= | tr -d ' '
    else
        echo "N/A"
    fi
}

# Check all services
services=(
    "dump1090.*--net:dump1090 (SDR Decoder)"
    "flight_logger_enhanced.py:Flight Logger"
    "log_server.py:Log API Server (port 8081)"
    "position_tracker.py:Position Tracker"
    "signal_logger.py:Signal Logger"
    "python.*http.server.*8080:Web Server (port 8080)"
)

echo "Services:"
echo ""

for service in "${services[@]}"; do
    IFS=':' read -r pattern name <<< "$service"

    if is_running "$pattern"; then
        uptime=$(get_uptime "$pattern")
        echo -e "  ${GREEN}✓${NC}  $name"
        echo -e "      Uptime: $uptime"
    else
        echo -e "  ${RED}✗${NC}  $name"
    fi
done

echo ""
echo "============================================================"
echo "  Database Statistics"
echo "============================================================"
echo ""

# Check database stats
if [ -f "flight_log.db" ]; then
    flights_total=$(sqlite3 flight_log.db "SELECT COUNT(*) FROM flights;" 2>/dev/null)
    flights_today=$(sqlite3 flight_log.db "SELECT COUNT(*) FROM flights WHERE DATE(first_seen) = DATE('now');" 2>/dev/null)
    positions=$(sqlite3 flight_log.db "SELECT COUNT(*) FROM signal_quality;" 2>/dev/null)

    echo "  Total flights logged:     $flights_total"
    echo "  Flights today:            $flights_today"
    echo "  Position updates logged:  $positions"
else
    echo -e "  ${RED}Database not found${NC}"
fi

echo ""
echo "============================================================"
echo "  Current Aircraft"
echo "============================================================"
echo ""

# Check current aircraft
if [ -f "dump1090-fa-web/public_html/data/aircraft.json" ]; then
    aircraft_count=$(python3 -c "import json; data=json.load(open('dump1090-fa-web/public_html/data/aircraft.json')); print(len(data.get('aircraft', [])))" 2>/dev/null)
    messages=$(python3 -c "import json; data=json.load(open('dump1090-fa-web/public_html/data/aircraft.json')); print(data.get('messages', 0))" 2>/dev/null)

    echo "  Aircraft in range:        $aircraft_count"
    echo "  Total messages received:  $messages"
else
    echo -e "  ${RED}Aircraft data not available${NC}"
fi

echo ""
echo "============================================================"
echo "  Quick Links"
echo "============================================================"
echo ""
echo "  Live Map:        http://localhost:8080/"
echo "  Statistics:      http://localhost:8080/stats.html"
echo "  Flight Log:      http://localhost:8080/log.html"
echo "  Signal Monitor:  http://localhost:8080/signal-monitor.html"
echo ""
echo "============================================================"
echo ""
