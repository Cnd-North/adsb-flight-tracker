#!/usr/bin/env python3
"""Setup signal quality logging in the database"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def setup_signal_table():
    """Create signal_quality table with optimized schema"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("=" * 70)
    print("SETTING UP SIGNAL QUALITY LOGGING")
    print("=" * 70)
    print()

    # Create signal_quality table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icao TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rssi REAL,
            latitude REAL,
            longitude REAL,
            altitude INTEGER,
            distance REAL,
            messages INTEGER,
            registration TEXT,
            callsign TEXT,
            aircraft_type TEXT,
            FOREIGN KEY (icao) REFERENCES flights(icao)
        )
    ''')

    print("✓ Created 'signal_quality' table")

    # Create indexes for fast queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_signal_timestamp
        ON signal_quality(timestamp)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_signal_icao
        ON signal_quality(icao, timestamp)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_signal_rssi
        ON signal_quality(rssi)
    ''')

    print("✓ Created indexes for fast queries")

    # Create aggregated stats table for long-term storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_stats_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour_timestamp TIMESTAMP NOT NULL,
            total_aircraft INTEGER,
            avg_rssi REAL,
            min_rssi REAL,
            max_rssi REAL,
            avg_distance REAL,
            max_distance REAL,
            total_messages INTEGER,
            UNIQUE(hour_timestamp)
        )
    ''')

    print("✓ Created 'signal_stats_hourly' table for aggregated data")

    conn.commit()

    # Show table info
    cursor.execute("PRAGMA table_info(signal_quality)")
    columns = cursor.fetchall()

    print()
    print("📊 Signal Quality Table Schema:")
    print()
    for col in columns:
        print(f"  • {col[1]:15s} {col[2]:10s}")

    # Check current size
    cursor.execute("SELECT COUNT(*) FROM signal_quality")
    count = cursor.fetchone()[0]

    print()
    print(f"Current signal records: {count}")

    # Show example query
    print()
    print("=" * 70)
    print("EXAMPLE QUERIES")
    print("=" * 70)
    print()

    print("📊 Average signal strength by hour:")
    print("""
    SELECT
        strftime('%H:00', timestamp) as hour,
        AVG(rssi) as avg_signal,
        COUNT(*) as samples
    FROM signal_quality
    WHERE date(timestamp) = date('now')
    GROUP BY hour
    ORDER BY hour;
    """)

    print()
    print("📍 Signal strength by direction:")
    print("""
    SELECT
        CASE
            WHEN latitude > (SELECT latitude FROM flights LIMIT 1) THEN 'North'
            ELSE 'South'
        END as direction,
        AVG(rssi) as avg_signal
    FROM signal_quality
    WHERE date(timestamp) = date('now')
    GROUP BY direction;
    """)

    print()
    print("✈️ Best/worst performing aircraft:")
    print("""
    SELECT
        registration,
        aircraft_type,
        AVG(rssi) as avg_signal,
        COUNT(*) as samples
    FROM signal_quality
    WHERE registration IS NOT NULL
    GROUP BY registration
    ORDER BY avg_signal DESC
    LIMIT 10;
    """)

    conn.close()

    print()
    print("=" * 70)
    print("✓ Signal quality logging is ready!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run: python3 signal_logger.py")
    print("  2. Or: Integrate into flight_logger_enhanced.py")
    print("  3. Run: python3 signal_analytics.py (for analysis)")

if __name__ == "__main__":
    setup_signal_table()
