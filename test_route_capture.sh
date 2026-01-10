#!/bin/bash
# Test script to monitor route capture in real-time

echo "=================================="
echo "ROUTE CAPTURE MONITOR"
echo "=================================="
echo ""
echo "Watching flight logger for route captures..."
echo "Press Ctrl+C to stop"
echo ""
echo "=================================="
echo ""

# Follow the log file and highlight route captures
tail -f ~/adsb-tracker/flight_logger.log | grep --line-buffered -E "(New flight detected|Route|→)" --color=always
