#!/usr/bin/env python3
"""
ADS-B Flight Information Tracker
Reads dump1090 data and enriches it with OpenSky Network API
"""

import json
import requests
import time
import os
from datetime import datetime

# Configuration
AIRCRAFT_JSON = os.path.expanduser("~/adsb-tracker/dump1090-fa-web/public_html/data/aircraft.json")
OPENSKY_API = "https://opensky-network.org/api/states/all"
UPDATE_INTERVAL = 10  # seconds
CACHE_DURATION = 300  # Cache API results for 5 minutes

# Cache for API results
api_cache = {}

def read_dump1090_data():
    """Read aircraft data from dump1090 JSON file"""
    try:
        with open(AIRCRAFT_JSON, 'r') as f:
            data = json.load(f)
            return data.get('aircraft', [])
    except Exception as e:
        print(f"Error reading dump1090 data: {e}")
        return []

def get_opensky_data(icao24):
    """Query OpenSky Network API for aircraft info"""
    # Check cache first
    if icao24 in api_cache:
        cached_time, cached_data = api_cache[icao24]
        if time.time() - cached_time < CACHE_DURATION:
            return cached_data

    try:
        # Query OpenSky Network
        url = f"{OPENSKY_API}?icao24={icao24.lower()}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Extract relevant info
            if data.get('states') and len(data['states']) > 0:
                state = data['states'][0]
                info = {
                    'callsign': state[1].strip() if state[1] else None,
                    'origin_country': state[2],
                    'last_contact': state[4],
                    'longitude': state[5],
                    'latitude': state[6],
                    'altitude': state[7],
                    'on_ground': state[8],
                    'velocity': state[9],
                    'heading': state[10],
                    'vertical_rate': state[11],
                }
                # Cache the result
                api_cache[icao24] = (time.time(), info)
                return info

        return None

    except requests.exceptions.Timeout:
        return {'error': 'API timeout'}
    except Exception as e:
        return {'error': str(e)}

def format_altitude(alt):
    """Format altitude in feet"""
    if alt is None:
        return "N/A"
    return f"{int(alt):,} ft"

def format_speed(speed):
    """Format speed in knots"""
    if speed is None:
        return "N/A"
    return f"{int(speed)} kts"

def format_heading(hdg):
    """Format heading in degrees"""
    if hdg is None:
        return "N/A"
    return f"{int(hdg)}°"

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def display_aircraft_list(aircraft_list):
    """Display formatted list of aircraft with enriched data"""
    clear_screen()

    print("=" * 120)
    print(f"ADS-B FLIGHT TRACKER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    print(f"{'ICAO':<8} {'Callsign':<10} {'Country':<15} {'Alt':<12} {'Speed':<10} {'Heading':<8} {'Messages':<8}")
    print("-" * 120)

    if not aircraft_list:
        print("No aircraft detected")
        print("-" * 120)
        return

    # Sort by signal strength (number of messages received)
    sorted_aircraft = sorted(aircraft_list, key=lambda x: x.get('messages', 0), reverse=True)

    for aircraft in sorted_aircraft:
        icao = aircraft.get('hex', 'N/A').upper()
        callsign = aircraft.get('flight', '').strip() or 'N/A'
        altitude = format_altitude(aircraft.get('altitude'))
        speed = format_speed(aircraft.get('speed'))
        heading = format_heading(aircraft.get('track'))
        messages = aircraft.get('messages', 0)

        # Try to get enriched data from OpenSky
        country = "Unknown"
        if messages > 10:  # Only query API for aircraft with good signal
            opensky_data = get_opensky_data(icao)
            if opensky_data and 'origin_country' in opensky_data:
                country = opensky_data['origin_country']

        print(f"{icao:<8} {callsign:<10} {country:<15} {altitude:<12} {speed:<10} {heading:<8} {messages:<8}")

    print("-" * 120)
    print(f"Total Aircraft: {len(aircraft_list)} | Updating every {UPDATE_INTERVAL}s")
    print("Press Ctrl+C to exit")
    print()

def main():
    """Main loop"""
    print("Starting ADS-B Flight Tracker...")
    print("Reading data from dump1090...")
    print()

    try:
        while True:
            aircraft_list = read_dump1090_data()
            display_aircraft_list(aircraft_list)
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
        print("Final cache stats:")
        print(f"  Cached aircraft: {len(api_cache)}")
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
