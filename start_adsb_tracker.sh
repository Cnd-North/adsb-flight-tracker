#!/bin/bash

# ADS-B Flight Tracker - Master Start Script
# Starts all components in the correct order with status indicators

echo "============================================================"
echo "  ADS-B Flight Tracker - Starting All Services"
echo "============================================================"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

# Configuration
DUMP1090_DATA_DIR="$HOME/adsb-tracker/dump1090-fa-web/public_html/data"
PROJECT_DIR="$HOME/adsb-tracker"
LOG_DIR="$PROJECT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for status
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to wait for a file to exist
wait_for_file() {
    local file="$1"
    local timeout=10
    local elapsed=0

    while [ ! -f "$file" ] && [ $elapsed -lt $timeout ]; do
        sleep 1
        elapsed=$((elapsed + 1))
    done

    [ -f "$file" ]
}

echo "Step 1/6: Checking dump1090..."
if is_running "dump1090.*--net"; then
    echo -e "  ${YELLOW}⚠${NC}  dump1090 already running"
else
    echo -e "  ${GREEN}▶${NC}  Starting dump1090..."
    cd "$PROJECT_DIR"
    nohup dump1090 --net --gain -10 --metric --write-json "$DUMP1090_DATA_DIR" \
        > "$LOG_DIR/dump1090.log" 2>&1 &
    sleep 3

    if is_running "dump1090.*--net"; then
        echo -e "  ${GREEN}✓${NC}  dump1090 started successfully"
    else
        echo -e "  ${RED}✗${NC}  Failed to start dump1090"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "Step 2/6: Checking flight logger..."
if is_running "flight_logger_enhanced.py"; then
    echo -e "  ${YELLOW}⚠${NC}  Flight logger already running"
else
    echo -e "  ${GREEN}▶${NC}  Starting flight logger..."
    cd "$PROJECT_DIR"
    nohup python3 -u flight_logger_enhanced.py \
        > "$LOG_DIR/flight_logger.log" 2>&1 &
    sleep 2

    if is_running "flight_logger_enhanced.py"; then
        echo -e "  ${GREEN}✓${NC}  Flight logger started successfully"
    else
        echo -e "  ${RED}✗${NC}  Failed to start flight logger"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "Step 3/6: Checking log API server..."
if is_running "log_server.py"; then
    echo -e "  ${YELLOW}⚠${NC}  Log server already running"
else
    echo -e "  ${GREEN}▶${NC}  Starting log API server..."
    cd "$PROJECT_DIR"
    nohup python3 log_server.py \
        > "$LOG_DIR/log_server.log" 2>&1 &
    sleep 2

    if is_running "log_server.py"; then
        echo -e "  ${GREEN}✓${NC}  Log server started successfully (port 8081)"
    else
        echo -e "  ${RED}✗${NC}  Failed to start log server"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "Step 4/6: Checking position tracker..."
if is_running "position_tracker.py"; then
    echo -e "  ${YELLOW}⚠${NC}  Position tracker already running"
else
    echo -e "  ${GREEN}▶${NC}  Starting position tracker..."
    cd "$PROJECT_DIR"
    nohup python3 position_tracker.py \
        > "$LOG_DIR/position_tracker.log" 2>&1 &
    sleep 2

    if is_running "position_tracker.py"; then
        echo -e "  ${GREEN}✓${NC}  Position tracker started successfully"
    else
        echo -e "  ${RED}✗${NC}  Failed to start position tracker"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "Step 5/6: Checking signal logger..."
if is_running "signal_logger.py"; then
    echo -e "  ${YELLOW}⚠${NC}  Signal logger already running"
else
    if [ -f "$PROJECT_DIR/signal_logger.py" ]; then
        echo -e "  ${GREEN}▶${NC}  Starting signal logger..."
        cd "$PROJECT_DIR"
        nohup python3 signal_logger.py \
            > "$LOG_DIR/signal_logger.log" 2>&1 &
        sleep 2

        if is_running "signal_logger.py"; then
            echo -e "  ${GREEN}✓${NC}  Signal logger started successfully"
        else
            echo -e "  ${RED}✗${NC}  Failed to start signal logger"
        fi
    else
        echo -e "  ${YELLOW}⊝${NC}  Signal logger not found (optional)"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "Step 6/6: Checking web server..."
if is_running "python.*http.server.*8080"; then
    echo -e "  ${YELLOW}⚠${NC}  Web server already running"
else
    echo -e "  ${GREEN}▶${NC}  Starting web server..."
    cd "$DUMP1090_DATA_DIR/.."
    nohup python3 -m http.server 8080 \
        > "$LOG_DIR/web_server.log" 2>&1 &
    sleep 2

    if is_running "python.*http.server.*8080"; then
        echo -e "  ${GREEN}✓${NC}  Web server started successfully (port 8080)"
    else
        echo -e "  ${RED}✗${NC}  Failed to start web server"
    fi
fi
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

echo "============================================================"
echo "  Status Summary"
echo "============================================================"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

# Check all services
services=(
    "dump1090.*--net:dump1090 (SDR Decoder)"
    "flight_logger_enhanced.py:Flight Logger"
    "log_server.py:Log API Server"
    "position_tracker.py:Position Tracker"
    "signal_logger.py:Signal Logger (optional)"
    "python.*http.server.*8080:Web Server"
)

all_running=true

for service in "${services[@]}"; do
    IFS=':' read -r pattern name <<< "$service"

    if is_running "$pattern"; then
        echo -e "  ${GREEN}✓${NC}  $name"
    else
        if [[ "$name" == *"optional"* ]]; then
            echo -e "  ${YELLOW}⊝${NC}  $name"
        else
            echo -e "  ${RED}✗${NC}  $name"
            all_running=false
        fi
    fi
done

# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "============================================================"
echo "  Access Your Tracker"
echo "============================================================"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "  Live Map:        http://localhost:8080/"
echo "  Statistics:      http://localhost:8080/stats.html"
echo "  Flight Log:      http://localhost:8080/log.html"
echo "  Signal Monitor:  http://localhost:8080/signal-monitor.html"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "============================================================"
echo "  Logs Location"
echo "============================================================"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "  Logs directory:  $LOG_DIR"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "  View live logs:"
echo "    tail -f $LOG_DIR/flight_logger.log"
echo "    tail -f $LOG_DIR/position_tracker.log"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "============================================================"
echo "  Management Commands"
echo "============================================================"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
echo "  Check status:    ./check_status.sh"
echo "  Stop all:        ./stop_adsb_tracker.sh"
echo "  View coverage:   python3 analyze_coverage.py"
# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""

if [ "$all_running" = true ]; then
    echo -e "${GREEN}All services running successfully!${NC} ✈️"
else
    echo -e "${YELLOW}Some services failed to start. Check logs for details.${NC}"
fi

# Start watchdog to monitor flight logger
nohup ~/adsb-tracker/watchdog.sh > /dev/null 2>&1 &

echo ""
