#!/usr/bin/env python3
"""
ADS-B Flight Logger
Logs all detected flights with route information from APIs
"""

import json
import requests
import sqlite3
import time
import os
from datetime import datetime

# Configuration
AIRCRAFT_JSON = os.path.expanduser("~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft.json")
DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")
OPENSKY_API = "https://opensky-network.org/api"
UPDATE_INTERVAL = 30  # Check for new aircraft every 30 seconds

# Track seen aircraft to avoid duplicates in same session
seen_flights = set()

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao TEXT NOT NULL,
            callsign TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origin_country TEXT,
            origin_airport TEXT,
            destination_airport TEXT,
            aircraft_type TEXT,
            registration TEXT,
            altitude_max INTEGER,
            speed_max INTEGER,
            messages_total INTEGER,
            flight_date DATE DEFAULT (DATE('now')),
            UNIQUE(icao, callsign, flight_date)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_callsign ON flights(callsign)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON flights(flight_date)
    ''')

    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {DATABASE}")

def get_aircraft_route(callsign):
    """
    Try to get flight route information from FlightAware API
    Note: This is a simplified version - you may need API key for full access
    """
    try:
        # Try FlightAware public data first (limited)
        # For full access, you'd need: https://flightaware.com/commercial/firehose/

        # Alternative: Try aviation-edge or similar APIs
        # For now, we'll return None and rely on OpenSky data
        return None
    except Exception as e:
        return None

def get_opensky_info(icao):
    """Get aircraft information from OpenSky Network"""
    try:
        # Get current state
        url = f"{OPENSKY_API}/states/all?icao24={icao.lower()}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('states') and len(data['states']) > 0:
                state = data['states'][0]
                return {
                    'origin_country': state[2],
                    'callsign': state[1].strip() if state[1] else None,
                }

        return None
    except Exception as e:
        print(f"  Error querying OpenSky: {e}")
        return None

def log_flight(aircraft):
    """Log flight to database"""
    icao = aircraft.get('hex', '').upper()
    callsign = aircraft.get('flight', '').strip()

    if not icao:
        return

    # Create unique key for this flight session
    flight_key = f"{icao}_{callsign}_{datetime.now().date()}"

    # Skip if we've already logged this flight today
    if flight_key in seen_flights:
        # Update last_seen and max values
        update_flight(aircraft)
        return

    print(f"\n📝 New flight detected: {callsign or icao}")

    # Get additional info from OpenSky
    opensky_info = get_opensky_info(icao)
    country = opensky_info.get('origin_country') if opensky_info else 'Unknown'

    # Try to get route info (placeholder - would need API key for real data)
    route_info = get_aircraft_route(callsign) if callsign else None

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO flights
            (icao, callsign, origin_country, altitude_max, speed_max, messages_total)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            icao,
            callsign or None,
            country,
            aircraft.get('altitude'),
            aircraft.get('speed'),
            aircraft.get('messages', 0)
        ))

        conn.commit()

        if cursor.rowcount > 0:
            seen_flights.add(flight_key)
            print(f"  ✓ Logged: {callsign or icao} ({country})")
            print(f"  📊 Altitude: {aircraft.get('altitude')} ft | Speed: {aircraft.get('speed')} kts")

    except sqlite3.IntegrityError:
        # Already exists for today
        pass
    finally:
        conn.close()

def update_flight(aircraft):
    """Update existing flight with new max values"""
    icao = aircraft.get('hex', '').upper()
    callsign = aircraft.get('flight', '').strip()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE flights
        SET last_seen = CURRENT_TIMESTAMP,
            altitude_max = MAX(altitude_max, ?),
            speed_max = MAX(speed_max, ?),
            messages_total = messages_total + ?
        WHERE icao = ? AND callsign = ? AND DATE(flight_date) = DATE('now')
    ''', (
        aircraft.get('altitude') or 0,
        aircraft.get('speed') or 0,
        aircraft.get('messages', 0),
        icao,
        callsign or ''
    ))

    conn.commit()
    conn.close()

def read_dump1090_data():
    """Read aircraft data from dump1090"""
    try:
        with open(AIRCRAFT_JSON, 'r') as f:
            data = json.load(f)
            return data.get('aircraft', [])
    except Exception as e:
        return []

def get_stats():
    """Get logging statistics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM flights')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM flights WHERE flight_date = DATE('now')")
    today = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT origin_country) FROM flights')
    countries = cursor.fetchone()[0]

    conn.close()

    return total, today, countries

def main():
    """Main logging loop"""
    print("=" * 80)
    print("ADS-B FLIGHT LOGGER")
    print("=" * 80)
    print()

    # Initialize database
    init_database()

    print(f"✓ Log file: {DATABASE}")
    print(f"✓ Update interval: {UPDATE_INTERVAL} seconds")
    print()

    total, today, countries = get_stats()
    print(f"📊 Current stats:")
    print(f"   Total flights logged: {total}")
    print(f"   Flights today: {today}")
    print(f"   Countries seen: {countries}")
    print()
    print("Starting flight logger... (Press Ctrl+C to stop)")
    print("=" * 80)

    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Read current aircraft
            aircraft_list = read_dump1090_data()

            # Log each aircraft with good signal
            new_count = 0
            for aircraft in aircraft_list:
                # Only log aircraft with reasonable signal (>20 messages)
                if aircraft.get('messages', 0) > 20:
                    messages_before = len(seen_flights)
                    log_flight(aircraft)
                    if len(seen_flights) > messages_before:
                        new_count += 1

            if new_count > 0:
                total, today, countries = get_stats()
                print(f"\n📊 [{timestamp}] Stats: {today} today | {total} total | {countries} countries")
            else:
                print(f"[{timestamp}] Monitoring... ({len(aircraft_list)} aircraft visible)")

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n")
        print("=" * 80)
        print("Shutting down flight logger")
        print("=" * 80)
        total, today, countries = get_stats()
        print(f"\nFinal statistics:")
        print(f"  Flights logged today: {today}")
        print(f"  Total flights in database: {total}")
        print(f"  Countries observed: {countries}")
        print(f"\nDatabase saved to: {DATABASE}")
        print(f"View your log at: http://localhost:8080/log.html")
        print()

if __name__ == "__main__":
    main()
