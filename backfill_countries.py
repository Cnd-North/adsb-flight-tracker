#!/usr/bin/env python3
"""Backfill country data for flights using registration prefixes"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

# Aircraft registration prefixes to country mapping
REGISTRATION_COUNTRY_PREFIXES = {
    'C-': 'Canada',
    'N': 'United States',
    'G-': 'United Kingdom',
    'D-': 'Germany',
    'F-': 'France',
    'I-': 'Italy',
    'JA': 'Japan',
    'HL': 'South Korea',
    'B-': 'China',
    'VH-': 'Australia',
    'ZK-': 'New Zealand',
    'XA-': 'Mexico',
    'XB-': 'Mexico',
    'XC-': 'Mexico',
    'CC-': 'Chile',
    'PT-': 'Brazil',
    'PR-': 'Brazil',
    'PP-': 'Brazil',
    'PH-': 'Netherlands',
    'OO-': 'Belgium',
    'LN-': 'Norway',
    'SE-': 'Sweden',
    'OH-': 'Finland',
    'EI-': 'Ireland',
    'HB-': 'Switzerland',
    'TC-': 'Turkey',
    'A6-': 'United Arab Emirates',
    'A7-': 'Qatar',
    'HZ-': 'Saudi Arabia',
    'VT-': 'India',
    '9M-': 'Malaysia',
    'HS-': 'Thailand',
    'RP-': 'Philippines',
    'YV-': 'Venezuela',
    'LV-': 'Argentina',
    'ZS-': 'South Africa',
}

def get_country_from_registration(registration):
    """Determine country from aircraft registration prefix"""
    if not registration:
        return None

    registration = registration.upper().strip()

    # Check each prefix (sorted by length, longest first to match more specific prefixes)
    for prefix, country in sorted(REGISTRATION_COUNTRY_PREFIXES.items(), key=lambda x: -len(x[0])):
        if registration.startswith(prefix):
            return country

    return None

def main():
    print("=" * 70)
    print("COUNTRY DATA BACKFILL")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get current stats
    cursor.execute("SELECT origin_country, COUNT(*) FROM flights GROUP BY origin_country ORDER BY COUNT(*) DESC")
    print("Current country distribution:")
    for country, count in cursor.fetchall():
        print(f"  {country}: {count}")
    print()

    # Find flights with Unknown country that have a registration
    cursor.execute('''
        SELECT icao, registration, origin_country
        FROM flights
        WHERE origin_country = 'Unknown'
        AND registration IS NOT NULL
        AND registration != ''
    ''')

    flights_to_update = cursor.fetchall()

    print(f"Found {len(flights_to_update)} flights with 'Unknown' country but have registration")
    print()

    updated = 0
    still_unknown = 0

    for icao, registration, old_country in flights_to_update:
        country = get_country_from_registration(registration)

        if country:
            cursor.execute('''
                UPDATE flights
                SET origin_country = ?
                WHERE icao = ?
            ''', (country, icao))

            updated += 1
            print(f"✓ {icao} ({registration}): Unknown → {country}")
        else:
            still_unknown += 1
            print(f"○ {icao} ({registration}): Still unknown (unrecognized prefix)")

    conn.commit()

    print()
    print("=" * 70)
    print(f"Updated {updated} flights with country data")
    print(f"Still unknown: {still_unknown} (unrecognized registration prefixes)")
    print("=" * 70)
    print()

    # Show updated stats
    cursor.execute("SELECT origin_country, COUNT(*) FROM flights GROUP BY origin_country ORDER BY COUNT(*) DESC")
    print("Updated country distribution:")
    for country, count in cursor.fetchall():
        print(f"  {country}: {count}")

    conn.close()

if __name__ == "__main__":
    main()
