#!/usr/bin/env python3
"""
Signal Quality Analytics

Analyze stored signal data to understand:
- Antenna performance by direction
- Aircraft signal characteristics
- Time-of-day patterns
- Distance/altitude correlations
- Weather/atmospheric effects
"""

import sqlite3
import os
from datetime import datetime, timedelta

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

def print_header(title):
    """Print formatted section header"""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()

def analyze_by_time_of_day(conn):
    """Analyze signal quality by hour of day"""
    print_header("📊 SIGNAL QUALITY BY TIME OF DAY")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            strftime('%H', timestamp) as hour,
            AVG(rssi) as avg_signal,
            MIN(rssi) as min_signal,
            MAX(rssi) as max_signal,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft_count
        FROM signal_quality
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY hour
        ORDER BY hour
    ''')

    results = cursor.fetchall()

    if not results:
        print("No data available yet. Start signal_logger.py to collect data.")
        return

    print(f"{'Hour':^6} {'Avg Signal':>12} {'Min':>8} {'Max':>8} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for hour, avg, min_sig, max_sig, samples, aircraft in results:
        signal_bar = "█" * int((avg + 50) / 2)  # Visual bar (-50 to 0 dBFS)
        print(f"{hour:>02s}:00  {avg:>10.1f} dB  {min_sig:>6.1f}  {max_sig:>6.1f}  "
              f"{samples:>10,}  {aircraft:>10}  {signal_bar}")

    # Identify best and worst hours
    cursor.execute('''
        SELECT
            strftime('%H', timestamp) as hour,
            AVG(rssi) as avg_signal
        FROM signal_quality
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY hour
        ORDER BY avg_signal DESC
        LIMIT 1
    ''')

    best = cursor.fetchone()
    if best:
        print()
        print(f"🌟 Best hour: {best[0]}:00 (avg {best[1]:.1f} dB)")

    cursor.execute('''
        SELECT
            strftime('%H', timestamp) as hour,
            AVG(rssi) as avg_signal
        FROM signal_quality
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY hour
        ORDER BY avg_signal ASC
        LIMIT 1
    ''')

    worst = cursor.fetchone()
    if worst:
        print(f"⚠️  Worst hour: {worst[0]}:00 (avg {worst[1]:.1f} dB)")

def analyze_by_direction(conn):
    """Analyze signal quality by geographic direction"""
    print_header("📍 SIGNAL QUALITY BY DIRECTION")

    cursor = conn.cursor()

    # Get receiver location (from most recent sample with lat/lon)
    cursor.execute('''
        SELECT latitude, longitude
        FROM signal_quality
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 1
    ''')

    receiver = cursor.fetchone()
    if not receiver:
        print("No position data available yet.")
        return

    receiver_lat, receiver_lon = receiver
    print(f"Receiver location: {receiver_lat:.4f}, {receiver_lon:.4f}")
    print()

    # Analyze by quadrant (N, S, E, W, NE, NW, SE, SW)
    cursor.execute(f'''
        SELECT
            CASE
                WHEN latitude >= {receiver_lat} AND longitude >= {receiver_lon} THEN 'NE'
                WHEN latitude >= {receiver_lat} AND longitude < {receiver_lon} THEN 'NW'
                WHEN latitude < {receiver_lat} AND longitude >= {receiver_lon} THEN 'SE'
                ELSE 'SW'
            END as direction,
            AVG(rssi) as avg_signal,
            MAX(distance) as max_range_km,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft
        FROM signal_quality
        WHERE latitude IS NOT NULL
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY direction
        ORDER BY avg_signal DESC
    ''')

    results = cursor.fetchall()

    print(f"{'Direction':^10} {'Avg Signal':>12} {'Max Range':>12} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for direction, avg_sig, max_range, samples, aircraft in results:
        signal_quality = "■" * int((avg_sig + 50) / 2)
        print(f"{direction:^10} {avg_sig:>10.1f} dB  {max_range:>9.1f} km  "
              f"{samples:>10,}  {aircraft:>10}  {signal_quality}")

def analyze_by_aircraft_type(conn):
    """Analyze which aircraft types have best/worst signals"""
    print_header("✈️ SIGNAL QUALITY BY AIRCRAFT TYPE")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            aircraft_type,
            AVG(rssi) as avg_signal,
            MIN(rssi) as min_signal,
            MAX(rssi) as max_signal,
            AVG(distance) as avg_distance,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft_count
        FROM signal_quality
        WHERE aircraft_type IS NOT NULL
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY aircraft_type
        HAVING samples >= 10
        ORDER BY avg_signal DESC
        LIMIT 20
    ''')

    results = cursor.fetchall()

    if not results:
        print("No aircraft type data available yet.")
        return

    print(f"{'Type':^8} {'Avg Signal':>12} {'Avg Dist':>10} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for atype, avg_sig, min_sig, max_sig, avg_dist, samples, aircraft in results:
        print(f"{atype:^8} {avg_sig:>10.1f} dB  {avg_dist:>8.1f} km  "
              f"{samples:>10,}  {aircraft:>10}")

def analyze_distance_correlation(conn):
    """Analyze signal strength vs distance"""
    print_header("📏 SIGNAL STRENGTH vs DISTANCE")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            CASE
                WHEN distance < 50 THEN '0-50 km'
                WHEN distance < 100 THEN '50-100 km'
                WHEN distance < 150 THEN '100-150 km'
                WHEN distance < 200 THEN '150-200 km'
                ELSE '200+ km'
            END as distance_range,
            AVG(rssi) as avg_signal,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft
        FROM signal_quality
        WHERE distance IS NOT NULL
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY distance_range
        ORDER BY MIN(distance)
    ''')

    results = cursor.fetchall()

    if not results:
        print("No distance data available yet.")
        return

    print(f"{'Distance':^12} {'Avg Signal':>12} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for dist_range, avg_sig, samples, aircraft in results:
        signal_bar = "▓" * max(1, int((avg_sig + 50) / 2))
        print(f"{dist_range:^12} {avg_sig:>10.1f} dB  {samples:>10,}  {aircraft:>10}  {signal_bar}")

def analyze_altitude_correlation(conn):
    """Analyze signal strength vs altitude"""
    print_header("🛫 SIGNAL STRENGTH vs ALTITUDE")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            CASE
                WHEN altitude < 5000 THEN 'Low (<5k ft)'
                WHEN altitude < 15000 THEN 'Medium (5-15k ft)'
                WHEN altitude < 30000 THEN 'High (15-30k ft)'
                ELSE 'Very High (>30k ft)'
            END as altitude_range,
            AVG(rssi) as avg_signal,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft
        FROM signal_quality
        WHERE altitude IS NOT NULL
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY altitude_range
        ORDER BY MIN(altitude)
    ''')

    results = cursor.fetchall()

    if not results:
        print("No altitude data available yet.")
        return

    print(f"{'Altitude':^20} {'Avg Signal':>12} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for alt_range, avg_sig, samples, aircraft in results:
        print(f"{alt_range:^20} {avg_sig:>10.1f} dB  {samples:>10,}  {aircraft:>10}")

def analyze_sunrise_sunset_effect(conn):
    """Analyze signal degradation during sunrise/sunset"""
    print_header("🌅 SUNRISE/SUNSET SIGNAL EFFECTS")

    cursor = conn.cursor()

    # Sunrise typically 6-8 AM, sunset 5-8 PM (approximate)
    cursor.execute('''
        SELECT
            CASE
                WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 6 AND 8 THEN 'Sunrise (6-8 AM)'
                WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 17 AND 19 THEN 'Sunset (5-7 PM)'
                WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 10 AND 16 THEN 'Midday (10-4 PM)'
                WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 0 AND 5 THEN 'Night (12-5 AM)'
                ELSE 'Other'
            END as period,
            AVG(rssi) as avg_signal,
            COUNT(*) as samples,
            COUNT(DISTINCT icao) as aircraft
        FROM signal_quality
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY period
        ORDER BY avg_signal DESC
    ''')

    results = cursor.fetchall()

    if not results:
        print("Not enough data yet.")
        return

    print(f"{'Period':^20} {'Avg Signal':>12} {'Samples':>10} {'Aircraft':>10}")
    print("-" * 70)

    for period, avg_sig, samples, aircraft in results:
        print(f"{period:^20} {avg_sig:>10.1f} dB  {samples:>10,}  {aircraft:>10}")

    print()
    print("💡 Tip: Compare sunrise/sunset with midday to see atmospheric effects")

def show_summary(conn):
    """Show overall summary statistics"""
    print_header("📊 OVERALL SUMMARY")

    cursor = conn.cursor()

    # Total records
    cursor.execute('SELECT COUNT(*) FROM signal_quality')
    total = cursor.fetchone()[0]

    # Date range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM signal_quality')
    date_range = cursor.fetchone()

    # Unique aircraft
    cursor.execute('SELECT COUNT(DISTINCT icao) FROM signal_quality')
    aircraft = cursor.fetchone()[0]

    # Average signal
    cursor.execute('SELECT AVG(rssi) FROM signal_quality WHERE timestamp >= datetime("now", "-24 hours")')
    avg_24h = cursor.fetchone()[0]

    # Storage size
    cursor.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()')
    db_size = cursor.fetchone()[0] / (1024 * 1024)  # MB

    print(f"Total signal samples: {total:,}")
    print(f"Unique aircraft tracked: {aircraft:,}")
    print(f"Data range: {date_range[0]} to {date_range[1]}")
    print(f"Average signal (24h): {avg_24h:.1f} dB" if avg_24h else "No data in last 24h")
    print(f"Database size: {db_size:.2f} MB")

def main():
    """Run all analytics"""
    if not os.path.exists(DATABASE):
        print(f"❌ Database not found: {DATABASE}")
        print("Run setup_signal_logging.py first")
        return

    conn = sqlite3.connect(DATABASE)

    try:
        show_summary(conn)
        analyze_by_time_of_day(conn)
        analyze_sunrise_sunset_effect(conn)
        analyze_by_direction(conn)
        analyze_distance_correlation(conn)
        analyze_altitude_correlation(conn)
        analyze_by_aircraft_type(conn)

        print()
        print("=" * 70)
        print("Analysis complete!")
        print("=" * 70)
        print()
        print("💡 Run 'python3 signal_logger.py' to collect more data")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
