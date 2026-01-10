#!/usr/bin/env python3
"""
Backfill Aircraft Data
Updates existing flights in database with aircraft details from OpenSky Network
"""

import sqlite3
import requests
import time
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def get_aircraft_details(icao):
    """Get aircraft details from OpenSky Network"""
    try:
        # OpenSky aircraft database
        url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao.lower()}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Convert Unix timestamp to year if built date exists
            built_year = None
            if data.get('built'):
                try:
                    from datetime import datetime
                    built_year = datetime.fromtimestamp(data['built'] / 1000).year
                except:
                    built_year = None

            return {
                'registration': data.get('registration'),
                'model': data.get('model'),
                'type': data.get('typecode'),
                'manufacturer': data.get('manufacturerName'),  # Fixed: was 'manufacturername'
                'built': built_year,
                'operator': data.get('operator'),
                'operator_callsign': data.get('operatorCallsign'),
                'operator_iata': data.get('operatorIata')
            }
        else:
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def backfill_aircraft_data():
    """Update all flights with missing aircraft data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find flights with missing aircraft data
    cursor.execute('''
        SELECT DISTINCT icao
        FROM flights
        WHERE (registration IS NULL OR aircraft_model IS NULL OR manufacturer IS NULL)
        AND icao IS NOT NULL
        ORDER BY first_seen DESC
    ''')

    flights_to_update = cursor.fetchall()
    total = len(flights_to_update)

    print("=" * 80)
    print("AIRCRAFT DATA BACKFILL")
    print("=" * 80)
    print(f"\nFound {total} unique aircraft to update")
    print("\nStarting backfill process...")
    print("=" * 80)
    print()

    updated_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, (icao,) in enumerate(flights_to_update, 1):
        print(f"[{idx}/{total}] Processing {icao}...", end=" ")

        # Get aircraft details from API
        details = get_aircraft_details(icao)

        if details and any(details.values()):
            # Update all flights with this ICAO
            cursor.execute('''
                UPDATE flights
                SET registration = COALESCE(registration, ?),
                    aircraft_type = COALESCE(aircraft_type, ?),
                    aircraft_model = COALESCE(aircraft_model, ?),
                    manufacturer = COALESCE(manufacturer, ?),
                    year_built = COALESCE(year_built, ?),
                    operator = COALESCE(operator, ?),
                    operator_callsign = COALESCE(operator_callsign, ?),
                    operator_iata = COALESCE(operator_iata, ?)
                WHERE icao = ?
            ''', (
                details.get('registration'),
                details.get('type'),
                details.get('model'),
                details.get('manufacturer'),
                details.get('built'),
                details.get('operator'),
                details.get('operator_callsign'),
                details.get('operator_iata'),
                icao
            ))

            conn.commit()

            if cursor.rowcount > 0:
                aircraft_info = f"{details.get('manufacturer', 'Unknown')} {details.get('model', '')}"
                reg = details.get('registration', 'N/A')
                year = f" ({details.get('built')})" if details.get('built') else ""
                print(f"✓ Updated: {aircraft_info}{year} - Reg: {reg}")
                updated_count += 1
            else:
                print("○ No changes needed")
                skipped_count += 1

        else:
            print("✗ No data available")
            failed_count += 1

        # Rate limiting - don't hammer the API
        if idx < total:
            time.sleep(1)  # 1 second delay between requests

    conn.close()

    print()
    print("=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✓ Successfully updated: {updated_count}")
    print(f"  ✗ No data found:        {failed_count}")
    print(f"  ○ Already had data:     {skipped_count}")
    print(f"  Total processed:        {total}")
    print()
    print("Database updated! Refresh http://localhost:8080/log.html to see changes.")
    print()

if __name__ == "__main__":
    try:
        backfill_aircraft_data()
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
        print("Partial updates have been saved to the database.")
