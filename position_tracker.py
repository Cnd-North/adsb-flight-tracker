#!/usr/bin/env python3
"""
Position Tracker - Log every aircraft position for coverage analysis
Logs lat/lon/altitude/RSSI every update to analyze antenna blind spots
"""

import json
import sqlite3
import time
import math
from datetime import datetime

DATABASE = 'flight_log.db'
AIRCRAFT_JSON = 'dump1090-fa-web/public_html/data/aircraft.json'
UPDATE_INTERVAL = 10  # seconds between checks

# Your antenna location (update these!)
ANTENNA_LAT = 49.0  # Replace with your actual latitude
ANTENNA_LON = -122.0  # Replace with your actual longitude

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance

def log_position(conn, aircraft):
    """Log a position update to the signal_quality table"""
    cursor = conn.cursor()

    icao = aircraft.get('hex', '').upper()
    if not icao:
        return

    # Extract position data
    lat = aircraft.get('lat')
    lon = aircraft.get('lon')
    altitude = aircraft.get('altitude') or aircraft.get('alt_baro') or aircraft.get('alt_geom')
    rssi = aircraft.get('rssi')
    messages = aircraft.get('messages', 0)

    # Optional fields
    callsign = aircraft.get('flight', '').strip()
    registration = aircraft.get('registration')
    aircraft_type = aircraft.get('t')

    # Skip if no position data
    if lat is None or lon is None:
        return

    # Calculate distance from antenna
    distance = haversine_distance(ANTENNA_LAT, ANTENNA_LON, lat, lon)

    try:
        cursor.execute('''
            INSERT INTO signal_quality
            (icao, rssi, latitude, longitude, altitude, distance, messages,
             callsign, registration, aircraft_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            icao,
            rssi,
            lat,
            lon,
            altitude,
            distance,
            messages,
            callsign if callsign else None,
            registration,
            aircraft_type
        ))

        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

def main():
    print("=" * 60)
    print("  ADS-B Position Tracker - Coverage Analysis")
    print("=" * 60)
    print(f"Database: {DATABASE}")
    print(f"Data source: {AIRCRAFT_JSON}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"Antenna location: {ANTENNA_LAT:.4f}°, {ANTENNA_LON:.4f}°")
    print()
    print("This will log every aircraft position to analyze coverage...")
    print("Press Ctrl+C to stop")
    print()

    conn = sqlite3.connect(DATABASE)

    positions_logged = 0
    aircraft_tracked = set()

    try:
        while True:
            try:
                # Read aircraft.json
                with open(AIRCRAFT_JSON, 'r') as f:
                    data = json.load(f)

                aircraft_list = data.get('aircraft', [])
                current_count = len(aircraft_list)

                if current_count > 0:
                    # Log positions for all aircraft
                    for aircraft in aircraft_list:
                        icao = aircraft.get('hex', '').upper()
                        if icao and log_position(conn, aircraft):
                            positions_logged += 1
                            aircraft_tracked.add(icao)

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Aircraft: {current_count} | "
                          f"Positions logged: {positions_logged} | "
                          f"Unique aircraft: {len(aircraft_tracked)}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No aircraft in range")

            except FileNotFoundError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Waiting for {AIRCRAFT_JSON}...")
            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Invalid JSON, skipping...")

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("  Position Tracking Stopped")
        print("=" * 60)
        print(f"Total positions logged: {positions_logged}")
        print(f"Unique aircraft tracked: {len(aircraft_tracked)}")
        print()
        print("To analyze your coverage, run:")
        print("  python3 analyze_coverage.py")
        print()

    finally:
        conn.close()

if __name__ == "__main__":
    main()
