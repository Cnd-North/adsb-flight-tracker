# ADS-B Aircraft Tracking & Logging Guide

Complete guide for running your ADS-B tracking system with flight logging capabilities.

---

## Quick Start - Complete System

### 1. Start dump1090 (ADS-B Decoder)

```bash
cd ~/radioconda
/usr/local/Cellar/dump1090-mutability/1.15_20180310-4a16df3-dfsg_3/bin/dump1090 \
  --net \
  --gain -10 \
  --metric \
  --write-json ~/radioconda/Projects/dump1090-fa-web/public_html/data \
  --quiet &
```

### 2. Start Web Server (Map Interface)

```bash
cd ~/radioconda/Projects/dump1090-fa-web/public_html
python3 -m http.server 8080 &
```

### 3. Start Enhanced Flight Logger (Logs All Flights to Database)

Automatically fetches aircraft details and operator info from OpenSky Network:

```bash
cd ~/radioconda/Projects
nohup python3 flight_logger_enhanced.py > flight_logger.log 2>&1 &
```

### 4. Start Log API Server (Serves Flight History)

```bash
cd ~/radioconda/Projects
nohup python3 log_server.py > log_server.log 2>&1 &
```

### 5. View Your Tracking System

Open your web browser:

- **Live Map**: http://localhost:8080
- **Live Table (with links)**: http://localhost:8080/flights.html
- **Flight Log (history)**: http://localhost:8080/log.html
- **Statistics & Analytics**: http://localhost:8080/stats.html

---

## Stopping Everything

### Stop All Services at Once

```bash
pkill -f dump1090
pkill -f "http.server 8080"
pkill -f flight_logger_enhanced.py
pkill -f log_server.py
```

### Stop Individual Services

```bash
# Stop dump1090 (ADS-B decoder)
pkill -f dump1090

# Stop web server
pkill -f "http.server 8080"

# Stop enhanced flight logger
pkill -f flight_logger_enhanced.py

# Stop log API server
pkill -f log_server.py
```

### Check What's Running

```bash
ps aux | grep -E "(dump1090|http.server|flight_logger_enhanced|log_server)" | grep -v grep
```

---

## Understanding Your System

### Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| dump1090 | - | Decodes ADS-B signals from RTL-SDR |
| Web Server | 8080 | Serves map interface and web pages |
| Enhanced Flight Logger | - | Stores all flights to SQLite database with aircraft details |
| Log API Server | 8081 | Serves flight history and analytics via REST API |

### Web Interfaces

| URL | Description |
|-----|-------------|
| http://localhost:8080 | Interactive map with aircraft positions |
| http://localhost:8080/flights.html | Live table with FlightAware links |
| http://localhost:8080/log.html | Historical flight log with operator, squawk, vertical rate |
| http://localhost:8080/stats.html | Comprehensive statistics and analytics dashboard |

### Data Files

- **Live aircraft data**: `~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft.json`
- **Enriched data**: `~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft_enriched.json`
- **Flight database**: `~/radioconda/Projects/flight_log.db`
- **Logger output**: `~/radioconda/Projects/flight_logger.log`
- **API server log**: `~/radioconda/Projects/log_server.log`

---

## Flight Logging Features

### What Gets Logged

Every detected aircraft with >20 messages gets logged with:

**Basic Flight Data:**
- ✈️ ICAO hex code (unique aircraft identifier)
- 📞 Callsign/Flight number
- 🌍 Country of registration (from OpenSky Network)
- 📊 Maximum altitude observed
- ⚡ Maximum speed recorded
- 📡 Total messages received
- ⏰ First seen & last seen timestamps
- 📅 Flight date
- ⏱️ Time in view (duration tracked)

**Aircraft Details (from OpenSky Network API):**
- ✈️ Registration number (tail number)
- 🏭 Manufacturer (Boeing, Airbus, etc.)
- 📐 Aircraft model (737-800, A320, etc.)
- 🏷️ Aircraft type code (B738, A320, etc.)
- 📅 Year built

**Operator Information:**
- 🏢 Operator/Airline name (Alaska Airlines, FedEx, etc.)
- 📻 Operator callsign
- 🏷️ IATA code

**Flight Dynamics:**
- 🔢 Squawk code (transponder code)
- ⚠️ Emergency status (7500/7600/7700 detection)
- 📈 Vertical rate (climb/descent in ft/min)
- 📍 Position (latitude/longitude)
- 📶 Signal strength (RSSI)

### Querying Your Flight Database

```bash
# View last 10 flights
sqlite3 ~/radioconda/Projects/flight_log.db \
  "SELECT * FROM flights ORDER BY first_seen DESC LIMIT 10"

# Count flights by country
sqlite3 ~/radioconda/Projects/flight_log.db \
  "SELECT origin_country, COUNT(*) as count FROM flights
   GROUP BY origin_country ORDER BY count DESC"

# Today's flights
sqlite3 ~/radioconda/Projects/flight_log.db \
  "SELECT callsign, icao, origin_country, altitude_max
   FROM flights WHERE flight_date = DATE('now')"

# Export all flights to CSV
sqlite3 -header -csv ~/radioconda/Projects/flight_log.db \
  "SELECT * FROM flights ORDER BY first_seen DESC" > myflights.csv
```

### Flight Log Statistics

View comprehensive analytics at: http://localhost:8080/stats.html

**Statistics Dashboard Includes:**
- 📊 Unique aircraft counter
- 🏭 Top 10 manufacturers with counts
- 📐 Most common aircraft models (bar chart)
- 🏢 Top operators/airlines you've tracked
- ⚠️ Emergency events log (7500/7600/7700 codes)
- 🌍 Aircraft by country breakdown
- ⏰ Flights by hour of day (24-hour chart)
- 🏔️ Altitude records (top 5 highest)
- ⚡ Speed records (top 5 fastest)
- 💎 Rare aircraft (seen only once)

Or query directly:

```bash
sqlite3 ~/radioconda/Projects/flight_log.db \
  "SELECT
    COUNT(*) as total_flights,
    COUNT(DISTINCT origin_country) as countries,
    MAX(altitude_max) as max_altitude,
    MAX(speed_max) as max_speed
   FROM flights"
```

---

## dump1090 Parameters Explained

- `--net` - Enable network connections for data output
- `--gain -10` - Use automatic gain control (recommended)
- `--gain 40` - Set manual gain to 40 dB (alternative)
- `--metric` - Display altitude/speed in meters/km instead of feet/miles
- `--write-json <dir>` - Write aircraft data to JSON files for web interface
- `--quiet` - Don't print messages to console
- `--interactive` - Show aircraft table in terminal (can't use with --quiet)

---

## Troubleshooting

### No Aircraft Showing Up?

1. **Check if dump1090 is running:**
   ```bash
   ps aux | grep dump1090
   ```

2. **Check if data files are being updated:**
   ```bash
   ls -lt ~/radioconda/Projects/dump1090-fa-web/public_html/data/
   cat ~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft.json
   ```

3. **Check RTL-SDR connection:**
   ```bash
   rtl_test -t
   ```

4. **Improve reception:**
   - Move antenna closer to window or outside
   - Try different window/location
   - Increase gain: `--gain 49.6` (maximum)

### Web Page Not Loading?

1. **Check if web server is running:**
   ```bash
   ps aux | grep "http.server"
   lsof -i :8080
   ```

2. **Try accessing directly:**
   ```bash
   curl http://localhost:8080
   ```

3. **Try a different port:**
   ```bash
   python3 -m http.server 8081
   ```
   Then visit: http://localhost:8081

### Flight Log Not Working?

1. **Check if logger is running:**
   ```bash
   ps aux | grep flight_logger_enhanced
   ```

2. **Check logger output:**
   ```bash
   tail -f ~/radioconda/Projects/flight_logger.log
   ```

3. **Backfill aircraft details for existing flights:**
   ```bash
   cd ~/radioconda/Projects
   python3 backfill_aircraft_data.py
   ```

4. **Check API server:**
   ```bash
   ps aux | grep log_server
   curl http://localhost:8081/api/stats
   curl http://localhost:8081/api/analytics
   ```

5. **Verify database exists:**
   ```bash
   ls -lh ~/radioconda/Projects/flight_log.db
   ```

### "Could not connect to API server" Error

1. **Restart log API server:**
   ```bash
   pkill -f log_server.py
   cd ~/radioconda/Projects
   nohup python3 log_server.py > log_server.log 2>&1 &
   ```

2. **Check if port 8081 is available:**
   ```bash
   lsof -i :8081
   ```

3. **Test API directly:**
   ```bash
   curl http://localhost:8081/api/flights
   ```

### RTL-SDR Already in Use?

If you get "usb_claim_interface error", another program is using your RTL-SDR.

**Check what's using it:**
```bash
lsof | grep rtl
```

**Common conflicts:**
- GNU Radio Companion is still running
- Another instance of dump1090
- GQRX is running

**Solution:** Kill the other program first:
```bash
pkill -f gnuradio-companion
pkill -f gqrx
```

---

## Advanced: Interactive Terminal Mode

See aircraft in your terminal instead of the web:

```bash
/usr/local/Cellar/dump1090-mutability/1.15_20180310-4a16df3-dfsg_3/bin/dump1090 \
  --interactive \
  --net \
  --gain -10 \
  --metric
```

Press `Ctrl+C` to stop.

Or use the custom flight tracker:

```bash
cd ~/radioconda/Projects
python3 flight_tracker.py
```

---

## Tips for Better Reception

1. **Antenna placement matters most:**
   - Higher = better (roof/attic is ideal)
   - Outside > inside
   - Clear line of sight to sky
   - Away from metal objects

2. **Aircraft altitude matters:**
   - High-altitude aircraft (30,000+ ft): visible 200-300 miles
   - Medium altitude (10,000-30,000 ft): 50-150 miles
   - Low-altitude (<10,000 ft): 20-50 miles
   - Ground aircraft: < 5 miles

3. **Time of day:**
   - More aircraft during daytime (6am-10pm)
   - Peak hours: morning (7-9am) and evening (5-7pm)
   - Check https://www.flightradar24.com to see what's flying near you

4. **Antenna upgrades:**
   - Stock antenna: 50-100 mile range
   - Better 1090 MHz antenna: 150-250 mile range
   - Outdoor antenna with LNA: 300+ mile range

---

## File Locations Reference

### Executables
- **dump1090**: `/usr/local/Cellar/dump1090-mutability/1.15_20180310-4a16df3-dfsg_3/bin/dump1090`
- **Python scripts**: `~/radioconda/Projects/`

### Web Interface
- **Base directory**: `~/radioconda/Projects/dump1090-fa-web/public_html/`
- **Map page**: `index.html`
- **Live table**: `flights.html`
- **Flight log**: `log.html`

### Data Files
- **Live aircraft**: `~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft.json`
- **Enriched data**: `~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft_enriched.json`
- **Flight database**: `~/radioconda/Projects/flight_log.db`

### Logs
- **Flight logger**: `~/radioconda/Projects/flight_logger.log`
- **API server**: `~/radioconda/Projects/log_server.log`

### GNU Radio
- **FM radio flowgraph**: `~/radioconda/Projects/untitled.grc`
- **ADS-B flowgraph**: `~/radioconda/Projects/adsb_rtlsdr.grc`

---

## Other SDR Projects

### FM Radio Receiver

```bash
cd ~/radioconda
./bin/gnuradio-companion ~/radioconda/Projects/untitled.grc
```

**Note:** Stop dump1090 first - only one program can use the RTL-SDR at a time!

### ADS-B with GNU Radio (Alternative)

```bash
cd ~/radioconda
./bin/gnuradio-companion ~/radioconda/Projects/adsb_rtlsdr.grc
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| **Start dump1090** | See "Quick Start" section above |
| **Start web server** | `cd ~/radioconda/Projects/dump1090-fa-web/public_html && python3 -m http.server 8080 &` |
| **Start flight logger** | `cd ~/radioconda/Projects && nohup python3 flight_logger_enhanced.py > flight_logger.log 2>&1 &` |
| **Start log API** | `cd ~/radioconda/Projects && nohup python3 log_server.py > log_server.log 2>&1 &` |
| **Stop all** | `pkill -f dump1090; pkill -f http.server; pkill -f flight_logger_enhanced; pkill -f log_server` |
| **View map** | http://localhost:8080 |
| **View live table** | http://localhost:8080/flights.html |
| **View flight log** | http://localhost:8080/log.html |
| **View statistics** | http://localhost:8080/stats.html |
| **Backfill aircraft data** | `cd ~/radioconda/Projects && python3 backfill_aircraft_data.py` |
| **Check status** | `ps aux \| grep -E "(dump1090\|http.server\|flight_logger_enhanced\|log_server)" \| grep -v grep` |
| **Export flights** | `sqlite3 -header -csv ~/radioconda/Projects/flight_log.db "SELECT * FROM flights" > flights.csv` |

---

## Startup Script (Optional)

Create a file `~/radioconda/Projects/start_adsb.sh`:

```bash
#!/bin/bash

echo "Starting ADS-B Tracking System..."

# Start dump1090
echo "Starting dump1090..."
/usr/local/Cellar/dump1090-mutability/1.15_20180310-4a16df3-dfsg_3/bin/dump1090 \
  --net \
  --gain -10 \
  --metric \
  --write-json ~/radioconda/Projects/dump1090-fa-web/public_html/data \
  --quiet &

sleep 2

# Start web server
echo "Starting web server on port 8080..."
cd ~/radioconda/Projects/dump1090-fa-web/public_html
python3 -m http.server 8080 > /dev/null 2>&1 &

sleep 1

# Start enhanced flight logger
echo "Starting enhanced flight logger..."
cd ~/radioconda/Projects
nohup python3 flight_logger_enhanced.py > flight_logger.log 2>&1 &

sleep 1

# Start log API server
echo "Starting log API server on port 8081..."
nohup python3 log_server.py > log_server.log 2>&1 &

sleep 2

echo ""
echo "✓ ADS-B Tracking System Started!"
echo ""
echo "Access your interfaces:"
echo "  Map:        http://localhost:8080"
echo "  Live Table: http://localhost:8080/flights.html"
echo "  Flight Log: http://localhost:8080/log.html"
echo "  Statistics: http://localhost:8080/stats.html"
echo ""
echo "To stop everything:"
echo "  ~/radioconda/Projects/stop_adsb.sh"
echo ""
```

Make it executable:

```bash
chmod +x ~/radioconda/Projects/start_adsb.sh
```

Create stop script `~/radioconda/Projects/stop_adsb.sh`:

```bash
#!/bin/bash

echo "Stopping ADS-B Tracking System..."

pkill -f dump1090
pkill -f "http.server 8080"
pkill -f flight_logger_enhanced.py
pkill -f log_server.py

echo "✓ All services stopped"
```

Make it executable:

```bash
chmod +x ~/radioconda/Projects/stop_adsb.sh
```

Then you can simply run:

```bash
# Start everything
~/radioconda/Projects/start_adsb.sh

# Stop everything
~/radioconda/Projects/stop_adsb.sh
```

---

## API Endpoints Reference

### Log API Server (Port 8081)

- **GET /api/flights** - Returns all logged flights with complete details as JSON
- **GET /api/stats** - Returns basic statistics (total flights, countries, max altitude/speed)
- **GET /api/analytics** - Returns comprehensive analytics for statistics dashboard

**Example Requests:**
```bash
# Get all flights with details
curl http://localhost:8081/api/flights | python3 -m json.tool

# Get basic statistics
curl http://localhost:8081/api/stats | python3 -m json.tool

# Get detailed analytics
curl http://localhost:8081/api/analytics | python3 -m json.tool
```

**Flight Data Fields Returned:**
- icao, callsign, registration
- first_seen, last_seen, flight_date, time_in_view
- origin_country, origin_airport, destination_airport
- altitude_max, speed_max, vertical_rate
- manufacturer, aircraft_model, aircraft_type, year_built
- operator, operator_callsign, operator_iata
- squawk, emergency
- latitude, longitude, signal_rssi
- messages_total

**Analytics Data Includes:**
- unique_aircraft (count)
- top_manufacturers (with counts)
- top_models (with counts)
- top_operators (with counts)
- emergencies (all emergency events)
- countries (breakdown by country)
- flights_by_hour (24-hour distribution)
- altitude_records (top 10)
- speed_records (top 10)
- rare_aircraft (seen only once)

---

Happy aircraft tracking! ✈️

**Questions or issues?**
- Check the troubleshooting section above
- Review log files in `~/radioconda/Projects/`
- Verify all services are running with `ps aux | grep -E "(dump1090|http|flight|log)"`
