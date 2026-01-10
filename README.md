# ✈️ ADS-B Flight Tracker Pro

A comprehensive, professional-grade ADS-B aircraft tracking system with intelligent route optimization, signal analysis, and beautiful web visualizations. Built for aviation enthusiasts who want to track, log, and analyze aircraft in their area with minimal API costs.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

![ADS-B Tracker Screenshot](docs/screenshot.png)

## 🌟 Features

### Core Tracking
- ✈️ **Real-time ADS-B aircraft tracking** via dump1090
- 📊 **SQLite database** with comprehensive flight logging
- 🗺️ **Interactive web map** with altitude-based aircraft coloring
- 📍 **Automatic route detection** (origin → destination airports)
- 🌍 **Country detection** from aircraft registrations

### Intelligent Route API Optimizer 🎯
- **Makes your 100 free API calls go 3-5x further!**
- Prioritizes military, private, cargo, and unique flights over common commercial routes
- Dynamic scoring system adjusts based on remaining quota
- Automatic route caching prevents duplicate API calls
- Detailed logging shows exactly why each flight was prioritized or skipped

### Data Quality & Management
- 🔧 **Automatic manufacturer normalization** - Consolidates variants (e.g., "The Boeing Company" → "Boeing")
- 🛠️ **OpenSky corruption fixes** - Corrects misidentified aircraft from corrupted database
- 🚫 **Duplicate removal** - Prevents same aircraft being logged multiple times
- ✅ **Data validation** - Verified against FlightRadar24, ADS-B Exchange, RadarBox

### Web Interface
- 📈 **Interactive statistics dashboard**
  - Click manufacturers to see their aircraft
  - Click aircraft models to see flight details
  - Rare aircraft gallery
  - Real-time system status monitoring
- 🗺️ **Live map with altitude-based colors**
  - Red (low) → Orange → Green → Blue → Purple (high altitude)
  - Flight tracks with altitude visualization
  - Country flags and detailed aircraft info
- 📡 **Signal quality monitor**
  - Real-time waterfall display (1090 MHz spectrum)
  - Signal strength graphs with dB scale legend
  - Message rate tracking
  - Time-of-day analysis
- 📋 **Advanced flight log** with comprehensive filtering
  - Date ranges, time of day, text search
  - Altitude, speed, vertical speed ranges
  - Squawk code filtering
  - CSV export

### Signal Analytics
- 📊 Historical signal quality logging to database
- 🔍 Pattern analysis (time-of-day, direction, aircraft type)
- 📈 Distance/altitude correlation analysis
- 🌅 Sunrise/sunset effects quantification
- 💾 Efficient storage (~260 MB/month @ 10-second sampling)

### Advanced Coverage Analysis 🎯
- 📡 **Antenna Location Estimation**
  - Automatic triangulation from aircraft positions
  - RSSI-weighted calculation for accuracy
  - Confidence ratings based on sample size
  - Height estimation using geometry
- 🗺️ **3D Signal Heatmap Visualization**
  - Altitude-sliced heatmaps (5 ranges: 0-50,000 ft)
  - Toggle overlay on/off with checkbox
  - Interactive altitude slider for single-range viewing
  - "Show All Altitudes" mode to display all 5 layers simultaneously
  - Color-coded signal strength (red=weak → green=strong)
  - Identify dead zones and terrain blocking
- 📊 **360° Coverage Polar Chart**
  - 16-direction compass coverage analysis
  - Signal strength color-coding by RSSI
  - Distance rings with km labels
  - Prominent N/E/S/W cardinal markers
  - Blind spot detection
  - Auto-scaling (max 10-11 rings)
- 📍 **Antenna Marker on Map**
  - Shows calculated antenna location with 📡 icon
  - Toggle antenna display on/off with checkbox
  - Range rings at 10, 20, 50, 100 km
  - Click for detailed location info

---

## 🛠️ Hardware Requirements

### Required Hardware

1. **RTL-SDR USB Dongle**
   - FlightAware Pro Stick Plus (recommended) - ~$25
   - Generic RTL2832U based dongle - ~$15-30
   - [Shop on Amazon](https://www.amazon.com/s?k=rtl-sdr&tag=electrobio-20) *

2. **1090 MHz ADS-B Antenna**
   - Outdoor antenna (best performance) - ~$30-60
   - Indoor antenna (works for nearby aircraft) - ~$20-40
   - [Shop on Amazon](https://www.amazon.com/s?k=1090+mhz+antenna&tag=electrobio-20) *

3. **Computer/Raspberry Pi**
   - Raspberry Pi 4 (2GB+ RAM recommended) - ~$45-75
   - Any Linux/Mac/Windows PC with USB port
   - [Raspberry Pi on Amazon](https://www.amazon.com/s?k=raspberry+pi+4&tag=electrobio-20) *

4. **Optional: Coax Cable**
   - Low-loss coax (LMR-400 or RG-6) if antenna is far from receiver
   - [Shop on Amazon](https://www.amazon.com/s?k=lmr-400&tag=electrobio-20) *

### Recommended Complete Kits

**Budget Setup (~$60-80):**
- Generic RTL-SDR dongle
- Indoor 1090 MHz antenna
- Raspberry Pi Zero 2 W

**Enthusiast Setup (~$120-150):**
- FlightAware Pro Stick Plus
- Outdoor 1090 MHz antenna with mounting bracket
- Raspberry Pi 4 (4GB)
- 10ft LMR-400 coax cable

**Pro Setup (~$200-300):**
- FlightAware Pro Stick Plus with built-in LNA
- High-gain outdoor collinear antenna
- Raspberry Pi 4 (8GB)
- 25ft LMR-400 coax cable
- Antenna mast and mounting hardware

\* *Affiliate links help support this project at no extra cost to you*

---

## 📋 Software Requirements

- **Python 3.8+**
- **dump1090** (or dump1090-fa, dump1090-mutability)
- **SQLite3**
- **Optional:** Aviation Stack API key (free tier: 100 calls/month)

### Python Dependencies
```bash
pip install requests
```

---

## 🚀 Quick Start

### 1. Install dump1090

**macOS (Homebrew):**
```bash
brew install dump1090-mutability
```

**Debian/Ubuntu/Raspberry Pi:**
```bash
sudo apt-get update
sudo apt-get install dump1090-fa
```

**From Source:**
```bash
git clone https://github.com/flightaware/dump1090.git
cd dump1090
make
```

### 2. Clone This Repository

```bash
cd ~
git clone https://github.com/Cnd-North/adsb-flight-tracker.git
cd adsb-flight-tracker
```

### 3. (Optional) Configure API Keys

**Aviation Stack** (for route data):
```bash
export AVIATIONSTACK_KEY='your-key-here'
```

Get your free API key at [aviationstack.com](https://aviationstack.com/product)

### 4. Start dump1090

```bash
dump1090 --net --gain -10 --metric --write-json ./dump1090-fa-web/public_html/data &
```

Or for dump1090-fa:
```bash
sudo systemctl start dump1090-fa
```

### 5. Start the Flight Logger

```bash
python3 flight_logger_enhanced.py
```

The database will be created automatically on first run.

### 6. Start the Log API Server

In a new terminal:
```bash
python3 log_server.py
```

### 7. View Your Tracking System

Open your browser to:
- **Live Map:** http://localhost:8080/ (includes signal heatmap overlay!)
- **Statistics:** http://localhost:8080/stats.html
- **Flight Log:** http://localhost:8080/log.html
- **Signal Monitor:** http://localhost:8080/signal-monitor.html (includes coverage analysis!)

### 8. Enable Signal Heatmap (Optional)

On the homepage, check the "🗺️ Signal Heatmap" box to see:
- Signal strength distribution across your coverage area
- Dead zones caused by terrain/buildings
- Coverage patterns at different altitudes (use slider)

---

## 📊 Intelligent Route Optimizer

The route optimizer makes your limited API calls count by intelligently prioritizing interesting flights:

### Priority Scoring System

| Flight Type | Score | Examples |
|-------------|-------|----------|
| 🎖️ Military | +100 | RCH345, SPAR12, NAVY456 |
| ✈️ Private/GA | +80 | N12345, C-GABC |
| 📦 Cargo | +60 | FDX1234, UPS789, GTI456 |
| 🌍 International | +30 | Non-US/Canada aircraft |
| 🔁 Common Routes (3+ times) | -100 | LAX-JFK, SFO-EWR |

### Dynamic Thresholds

The system adjusts its selectivity based on remaining API quota:

- **>50 calls:** Threshold = 20 (generous)
- **20-50 calls:** Threshold = 50 (prioritize interesting)
- **5-20 calls:** Threshold = 80 (cargo/private/military only)
- **<5 calls:** Threshold = 100 (military/exceptional only)

This means your 100 free API calls can track 200-300 flights by skipping common commercial routes!

---

## 📁 Project Structure

This repository contains **875 files** organized into the following structure:

### 🎯 Core Flight Tracking (~50 custom files)
```
adsb-flight-tracker/
├── flight_logger_enhanced.py      # Main flight logger with intelligent route detection
├── flight_logger.py                # Legacy/simple flight logger (use enhanced version)
├── flight_tracker.py               # Alternative tracker implementation
├── position_tracker.py             # Aircraft position logging and tracking
└── log_server.py                   # REST API server (port 8081) for web interface
```

### 📡 Signal Analysis & Coverage
```
├── signal_logger.py                # Historical signal quality data collection
├── signal_analytics.py             # Signal pattern analysis and statistics
├── signal_diagnostics.py           # Signal troubleshooting and debugging
├── signal_storage_analysis.py      # Database storage usage analysis
├── analyze_coverage.py             # Coverage area analysis and visualization
└── calculate_antenna_location.py   # Antenna position estimation from aircraft data
```

### 🔧 Data Quality & Maintenance
```
├── normalize_manufacturers.py      # Consolidate manufacturer name variants
├── remove_duplicates_simple.py     # Remove duplicate flight entries
├── remove_duplicates.py            # Advanced duplicate detection
├── fix_corrupted_aircraft.py       # Fix OpenSky database corruption
├── fix_bad_aircraft_data.py        # General data quality fixes
└── fix_flair_aircraft.py           # Fix Flair Airlines specific data issues
```

### 💾 Database Management & Backfill
```
├── setup_signal_logging.py         # Signal logging table setup (flights table auto-created)
├── backfill_aircraft_data.py       # Backfill missing aircraft information
├── backfill_aircraft_types.py      # Backfill aircraft type/model data
├── backfill_countries.py           # Backfill country data from registrations
├── backfill_routes_once.py         # One-time route data backfill
├── enhanced_opensky_backfill.py    # Enhanced OpenSky Network data import
└── enrich_aircraft_data.py         # Add additional aircraft metadata
```

### 🛤️ Route & API Management
```
├── route_optimizer.py              # Intelligent route API call prioritization
├── api_quota_manager.py            # API quota tracking and management
├── fetch_routes.py                 # Manual route data fetching
└── adsbexchange_routes.py          # ADS-B Exchange route integration
```

### 🧪 Testing & Diagnostics
```
├── test_callsign_conversion.py     # Test airline code conversions
├── test_opensky_quick.py           # Test OpenSky Network API
├── test_quota_integration.py       # Test quota management system
├── test_route_api.py               # Test route API functionality
└── test_route_capture.sh           # Shell script for route testing
```

### ⚙️ System Management Scripts
```
├── start_adsb_tracker.sh           # Master startup script for all services
├── stop_adsb_tracker.sh            # Gracefully stop all services
├── check_status.sh                 # Check status of all running services
└── watchdog.sh                     # Auto-restart crashed services
```

### 🌐 Web Interface (dump1090-fa-web/) - ~825 files
This is the FlightAware dump1090 web interface, customized with additional features:

```
dump1090-fa-web/
├── public_html/                    # Web interface root (served on port 8080)
│   ├── index.html                  # Live map with real-time aircraft tracking
│   ├── stats.html                  # Interactive statistics dashboard
│   ├── log.html                    # Advanced flight log with filters
│   ├── signal-monitor.html         # Signal quality + coverage analysis
│   ├── config.js                   # Map configuration
│   ├── script.js                   # Main application logic
│   ├── planeObject.js              # Aircraft object handling
│   ├── formatter.js                # Data formatting utilities
│   │
│   ├── Custom Visualization Modules:
│   ├── heatmap.js                  # 3D signal strength heatmap (5 altitude layers)
│   ├── coverage_viz.js             # 360° polar coverage chart
│   ├── antenna_marker.js           # Antenna location marker with range rings
│   ├── homepage_status.js          # Real-time system status widget
│   └── status_indicator.js         # Floating status panel
│   │
│   ├── flags-tiny/                 # Country flag icons
│   ├── images/                     # Aircraft silhouettes and UI icons
│   ├── geojson/                    # Geographical boundary data
│   ├── ol3/                        # OpenLayers 3 mapping library
│   ├── noUiSlider/                 # Altitude slider control
│   ├── jquery/                     # jQuery library
│   ├── style.css                   # Main stylesheet
│   └── data/                       # dump1090 JSON output (gitignored)
│
├── C source code (~500 files)      # dump1090 decoder (FlightAware fork)
│   ├── dump1090.c                  # Main ADS-B decoder
│   ├── net_io.c                    # Network I/O handling
│   ├── demod_2400.c                # 2.4 Msps demodulator
│   ├── track.c                     # Aircraft tracking logic
│   └── ...                         # Additional decoder components
│
└── Tools & Documentation
    ├── README.md                   # dump1090 documentation
    ├── README-json.md              # JSON output format spec
    └── tools/                      # Database and utility tools
```

### 📚 Documentation Files
```
├── README.md                       # This file - comprehensive project guide
├── README_GITHUB.md                # GitHub-specific readme
├── ADS-B_Guide.md                  # ADS-B protocol technical guide
├── HARDWARE_GUIDE.md               # Hardware selection and setup
├── ROUTE_SETUP_GUIDE.md            # API configuration instructions
├── QUOTA_MANAGEMENT_GUIDE.md       # API efficiency strategies
├── COVERAGE_FEATURES.md            # Coverage analysis documentation
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # MIT license
├── .gitignore                      # Excludes databases, logs, personal data
└── docs/                           # Additional documentation
    ├── HARDWARE_GUIDE.md
    ├── ROUTE_SETUP_GUIDE.md
    └── QUOTA_MANAGEMENT_GUIDE.md
```

### 📊 Auto-Generated Data (gitignored)
```
├── flight_log.db                   # SQLite database (auto-created on first run)
├── flight_log.db-shm               # Shared memory file (WAL mode)
├── flight_log.db-wal               # Write-ahead log (WAL mode)
├── .api_quota.json                 # API quota tracking state
└── logs/                           # Service logs directory
    ├── dump1090.log
    ├── flight_logger.log
    ├── log_server.log
    ├── position_tracker.log
    ├── signal_logger.log
    └── web_server.log
```

### 🗂️ File Categories Summary

- **Custom Python scripts:** ~40 files for flight tracking, signal analysis, and data management
- **Custom shell scripts:** 4 system management scripts
- **dump1090-fa-web:** ~825 files (FlightAware's web interface + customizations)
- **Documentation:** 10+ markdown files
- **Auto-generated:** Database, logs, and runtime data (excluded from git)

**Total repository size:** 875 tracked files (personal data excluded via .gitignore)

---

## 🔧 Configuration

### Environment Variables

```bash
# Aviation Stack API (optional, for route data)
export AVIATIONSTACK_KEY='your-key-here'

# Database location (optional, default: ~/radioconda/Projects/flight_log.db)
export FLIGHT_DB_PATH='/path/to/flight_log.db'

# dump1090 data location (optional)
export DUMP1090_DATA='/path/to/dump1090/data'
```

### Advanced Configuration

Edit `flight_logger_enhanced.py` to customize:
- `UPDATE_INTERVAL` - How often to check for new aircraft (default: 30 seconds)
- Route API preferences and fallbacks
- Custom airline ICAO to IATA mappings

Edit `route_optimizer.py` to customize:
- Military callsign patterns
- Cargo airline codes
- Common routes to deprioritize
- Priority scoring weights

---

## 📈 Usage Tips

### Maximizing API Efficiency

1. **Let the optimizer run for a few days** - It learns common routes in your area
2. **Monitor quota usage:** `python3 api_quota_manager.py status`
3. **Adjust thresholds** if you're in a high-traffic area
4. **Common routes are cached** - The system won't call API for repeat flights

### Signal Quality Optimization

1. **Position your antenna high** - Rooftop/attic is best
2. **Minimize obstacles** - Clear line of sight to the sky
3. **Use quality coax** - Low-loss cable if >10 feet from receiver
4. **Run signal analytics:** `python3 signal_analytics.py`
5. **Check the signal monitor** - http://localhost:8080/signal-monitor.html

### Data Quality

Run these scripts periodically to maintain clean data:
```bash
python3 normalize_manufacturers.py    # Fix manufacturer name variants
python3 remove_duplicates_simple.py   # Remove duplicate entries
python3 fix_corrupted_aircraft.py     # Fix OpenSky database corruption
```

---

## 🐛 Troubleshooting

### No Aircraft Detected

1. **Check dump1090 is running:**
   ```bash
   ps aux | grep dump1090
   ```

2. **Check RTL-SDR is connected:**
   ```bash
   lsusb | grep -i realtek
   rtl_test -t
   ```

3. **Verify antenna connection** - Check coax connectors are tight

4. **Check signal monitor** - http://localhost:8080/signal-monitor.html
   - You should see a waterfall display even without aircraft

### API Quota Exhausted

1. **Check remaining quota:**
   ```bash
   python3 api_quota_manager.py status
   ```

2. **Quota resets on 1st of each month** - Wait for reset or upgrade plan

3. **Optimizer will automatically skip API calls** when quota is depleted

### Web Interface Not Loading

1. **Check log API server is running:**
   ```bash
   ps aux | grep log_server
   ```

2. **Restart the server:**
   ```bash
   pkill -f log_server.py
   python3 log_server.py &
   ```

3. **Check firewall settings** - Ensure port 8080 and 8081 are open

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🐛 **Report bugs** - Open an issue with details
2. 💡 **Suggest features** - Share your ideas
3. 🔧 **Submit PRs** - Fix bugs or add features
4. 📖 **Improve docs** - Help others get started
5. ⭐ **Star this repo** - Show your support!

### Development Setup

```bash
git clone https://github.com/Cnd-North/adsb-flight-tracker.git
cd adsb-flight-tracker
# Make your changes
git checkout -b feature/your-feature
git commit -am "Add your feature"
git push origin feature/your-feature
# Open a Pull Request
```

---

## 📜 License

MIT License - feel free to use this project for personal or commercial purposes.

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FlightAware** - dump1090 software
- **OpenSky Network** - Aircraft database
- **Aviation Stack** - Route API
- **ADS-B Exchange** - Community data
- All contributors and aviation enthusiasts who make this hobby amazing!

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Cnd-North/adsb-flight-tracker/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Cnd-North/adsb-flight-tracker/discussions)
- **Wiki:** [Project Wiki](https://github.com/Cnd-North/adsb-flight-tracker/wiki)

---

## ⚠️ Disclaimer

This software is for educational and hobbyist purposes. ADS-B data is unencrypted and publicly available. Always respect privacy and follow local regulations regarding aircraft tracking. Do not use this software for flight safety or navigation purposes.

---

## ☕ Support This Project

If you find this project useful, consider:
- ⭐ Starring this repository
- 🐛 Reporting bugs and suggesting features
- 🛒 Using the affiliate links above when purchasing hardware (helps support development)
- ☕ [Buy me a coffee](https://buymeacoffee.com/electrobio)

Happy tracking! ✈️📡

---

**Made with ❤️ by aviation enthusiasts, for aviation enthusiasts**
