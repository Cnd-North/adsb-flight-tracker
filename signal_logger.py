#!/usr/bin/env python3
"""
Signal Quality Logger

Samples aircraft signal data every 10 seconds and stores in database.
Runs independently alongside flight_logger_enhanced.py
"""

import requests
import sqlite3
import time
import math
from datetime import datetime
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")
DUMP1090_URL = "http://localhost:8080/data/aircraft.json"
SAMPLE_INTERVAL = 10  # seconds

# Receiver location (will be auto-detected from dump1090)
RECEIVER_LAT = None
RECEIVER_LON = None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    if None in [lat1, lon1, lat2, lon2]:
        return None

    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def fetch_aircraft_data():
    """Fetch current aircraft data from dump1090"""
    try:
        response = requests.get(DUMP1090_URL, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def log_signal_sample(conn, aircraft):
    """Log a signal quality sample for one aircraft"""
    global RECEIVER_LAT, RECEIVER_LON

    icao = aircraft.get('hex', '').upper()
    if not icao:
        return

    # Get position data
    lat = aircraft.get('lat')
    lon = aircraft.get('lon')
    alt = aircraft.get('alt_baro')

    # Calculate distance if we have position
    distance = None
    if lat and lon and RECEIVER_LAT and RECEIVER_LON:
        distance = calculate_distance(RECEIVER_LAT, RECEIVER_LON, lat, lon)

    # Get signal data
    rssi = aircraft.get('rssi')  # Signal strength in dBFS
    messages = aircraft.get('messages', 0)

    # Get aircraft identifiers
    registration = aircraft.get('r')  # Registration from aircraft.json
    callsign = aircraft.get('flight', '').strip() or None
    aircraft_type = aircraft.get('t')  # Type code from aircraft.json

    # Only log if we have signal data
    if rssi is not None:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO signal_quality
            (icao, rssi, latitude, longitude, altitude, distance, messages,
             registration, callsign, aircraft_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (icao, rssi, lat, lon, alt, distance, messages,
              registration, callsign, aircraft_type))

def aggregate_hourly_stats(conn):
    """Create hourly aggregated statistics"""
    cursor = conn.cursor()

    # Get current hour
    current_hour = datetime.now().strftime('%Y-%m-%d %H:00:00')

    # Aggregate stats for the past hour
    cursor.execute('''
        INSERT OR REPLACE INTO signal_stats_hourly
        (hour_timestamp, total_aircraft, avg_rssi, min_rssi, max_rssi,
         avg_distance, max_distance, total_messages)
        SELECT
            ?,
            COUNT(DISTINCT icao),
            AVG(rssi),
            MIN(rssi),
            MAX(rssi),
            AVG(distance),
            MAX(distance),
            SUM(messages)
        FROM signal_quality
        WHERE timestamp >= datetime(?, '-1 hour')
        AND timestamp < ?
    ''', (current_hour, current_hour, current_hour))

def cleanup_old_data(conn):
    """Remove signal data older than 7 days"""
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM signal_quality
        WHERE timestamp < datetime('now', '-7 days')
    ''')

    deleted = cursor.rowcount
    if deleted > 0:
        print(f"🗑️  Cleaned up {deleted} old signal records (>7 days)")

    # Vacuum database to reclaim space
    cursor.execute('VACUUM')

def main():
    """Main signal logging loop"""
    global RECEIVER_LAT, RECEIVER_LON

    print("=" * 70)
    print("SIGNAL QUALITY LOGGER")
    print("=" * 70)
    print()
    print(f"Sample interval: {SAMPLE_INTERVAL} seconds")
    print(f"Database: {DATABASE}")
    print(f"Source: {DUMP1090_URL}")
    print()

    # Try to detect receiver location
    try:
        data = fetch_aircraft_data()
        if data and 'lat' in data and 'lon' in data:
            RECEIVER_LAT = data['lat']
            RECEIVER_LON = data['lon']
            print(f"📍 Receiver location: {RECEIVER_LAT:.4f}, {RECEIVER_LON:.4f}")
        else:
            print("⚠️  Receiver location not available from dump1090")
            print("   Distance calculations will be skipped")
    except:
        print("⚠️  Could not detect receiver location")

    print()
    print("Starting signal quality logging...")
    print("Press Ctrl+C to stop")
    print()

    conn = sqlite3.connect(DATABASE)
    sample_count = 0
    last_cleanup = datetime.now()
    last_hourly = datetime.now().hour

    try:
        while True:
            data = fetch_aircraft_data()

            if data and 'aircraft' in data:
                aircraft_list = data['aircraft']
                logged = 0

                for aircraft in aircraft_list:
                    log_signal_sample(conn, aircraft)
                    logged += 1

                conn.commit()
                sample_count += 1

                now = datetime.now()
                print(f"[{now.strftime('%H:%M:%S')}] Logged {logged} aircraft signals "
                      f"(sample #{sample_count})")

                # Create hourly aggregates
                if now.hour != last_hourly:
                    aggregate_hourly_stats(conn)
                    last_hourly = now.hour
                    print(f"  ✓ Created hourly stats for hour {last_hourly}")

                # Daily cleanup at midnight
                if (now - last_cleanup).days >= 1:
                    cleanup_old_data(conn)
                    last_cleanup = now

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("Signal logging stopped")
        print("=" * 70)

        # Show summary
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM signal_quality')
        total_records = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(DISTINCT icao) FROM signal_quality
            WHERE date(timestamp) = date('now')
        ''')
        today_aircraft = cursor.fetchone()[0]

        print()
        print(f"📊 Summary:")
        print(f"  Total signal records: {total_records:,}")
        print(f"  Aircraft tracked today: {today_aircraft}")
        print(f"  Samples collected: {sample_count}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
