#!/usr/bin/env python3
"""
Enhanced OpenSky Network Data Backfill
Uses multiple OpenSky APIs to fill missing aircraft and route data
"""

import sqlite3
import requests
import time
import os
from datetime import datetime, timedelta

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def get_aircraft_metadata(icao):
    """Get aircraft details from OpenSky metadata API"""
    try:
        url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao.lower()}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Convert Unix timestamp to year
            built_year = None
            if data.get('built'):
                try:
                    built_year = datetime.fromtimestamp(data['built'] / 1000).year
                except:
                    built_year = None

            return {
                'registration': data.get('registration'),
                'model': data.get('model'),
                'type': data.get('typecode'),
                'manufacturer': data.get('manufacturerName'),
                'operator': data.get('operator'),
                'operator_callsign': data.get('operatorCallsign'),
                'operator_iata': data.get('operatorIata'),
                'built': built_year
            }
    except Exception as e:
        print(f"    Metadata error: {e}")

    return None

def get_flight_routes(icao, first_seen):
    """Get flight route from OpenSky flights API"""
    try:
        # Query flights for this aircraft in a time window around first_seen
        # OpenSky uses Unix timestamps
        flight_time = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
        begin = int((flight_time - timedelta(hours=2)).timestamp())
        end = int((flight_time + timedelta(hours=2)).timestamp())

        url = f"https://opensky-network.org/api/flights/aircraft"
        params = {
            'icao24': icao.lower(),
            'begin': begin,
            'end': end
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Find flight closest to our first_seen time
                closest_flight = min(data, key=lambda f: abs(f.get('firstSeen', 0) - flight_time.timestamp()))

                origin = closest_flight.get('estDepartureAirport')
                dest = closest_flight.get('estArrivalAirport')

                # OpenSky sometimes returns empty strings
                return {
                    'origin': origin if origin and origin.strip() else None,
                    'destination': dest if dest and dest.strip() else None
                }
    except Exception as e:
        print(f"    Routes error: {e}")

    return None

def get_current_state(icao):
    """Get current state vector for additional info"""
    try:
        url = f"https://opensky-network.org/api/states/all"
        params = {'icao24': icao.lower()}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('states') and len(data['states']) > 0:
                state = data['states'][0]
                # State vector: [icao24, callsign, origin_country, ...]
                return {
                    'origin_country': state[2] if len(state) > 2 else None
                }
    except Exception as e:
        print(f"    State error: {e}")

    return None

def backfill_enhanced():
    """Enhanced backfill using multiple OpenSky endpoints"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get flights with missing data
    cursor.execute('''
        SELECT DISTINCT icao, callsign, first_seen
        FROM flights
        WHERE (manufacturer IS NULL OR manufacturer = '')
           OR (operator IS NULL OR operator = '')
           OR (origin_airport IS NULL AND destination_airport IS NULL)
        ORDER BY first_seen DESC
    ''')

    flights_to_update = cursor.fetchall()
    total = len(flights_to_update)

    print("=" * 80)
    print("ENHANCED OPENSKY NETWORK BACKFILL")
    print("=" * 80)
    print(f"\nFound {total} flights with missing data")
    print("\nUsing OpenSky Network APIs:")
    print("  1. Aircraft Metadata API (aircraft details)")
    print("  2. Flights API (route information)")
    print("  3. State Vectors API (country info)")
    print("\nStarting backfill...")
    print("=" * 80)
    print()

    updated_count = 0
    failed_count = 0

    for idx, (icao, callsign, first_seen) in enumerate(flights_to_update, 1):
        print(f"[{idx}/{total}] {icao} ({callsign or 'NO CALL'})...")

        # Try metadata API (free, no auth needed)
        metadata = get_aircraft_metadata(icao)
        time.sleep(1)  # Rate limiting

        # Skip routes API - requires authentication
        routes = None
        # routes = get_flight_routes(icao, first_seen)  # 403 Forbidden without auth

        # Update if we got any data
        if metadata or routes:
            updates = []
            params = []

            if metadata:
                if metadata.get('manufacturer'):
                    updates.append("manufacturer = COALESCE(manufacturer, ?)")
                    params.append(metadata['manufacturer'])
                if metadata.get('model'):
                    updates.append("aircraft_model = COALESCE(aircraft_model, ?)")
                    params.append(metadata['model'])
                if metadata.get('type'):
                    updates.append("aircraft_type = COALESCE(aircraft_type, ?)")
                    params.append(metadata['type'])
                if metadata.get('registration'):
                    updates.append("registration = COALESCE(registration, ?)")
                    params.append(metadata['registration'])
                if metadata.get('operator'):
                    updates.append("operator = COALESCE(operator, ?)")
                    params.append(metadata['operator'])
                if metadata.get('operator_callsign'):
                    updates.append("operator_callsign = COALESCE(operator_callsign, ?)")
                    params.append(metadata['operator_callsign'])
                if metadata.get('operator_iata'):
                    updates.append("operator_iata = COALESCE(operator_iata, ?)")
                    params.append(metadata['operator_iata'])
                if metadata.get('built'):
                    updates.append("year_built = COALESCE(year_built, ?)")
                    params.append(metadata['built'])

            if routes:
                if routes.get('origin'):
                    updates.append("origin_airport = COALESCE(origin_airport, ?)")
                    params.append(routes['origin'])
                if routes.get('destination'):
                    updates.append("destination_airport = COALESCE(destination_airport, ?)")
                    params.append(routes['destination'])

            if updates:
                sql = f'''
                    UPDATE flights
                    SET {', '.join(updates)}
                    WHERE icao = ?
                '''
                params.append(icao)

                cursor.execute(sql, params)
                conn.commit()

                # Show what we updated
                updates_made = []
                if metadata and metadata.get('manufacturer'):
                    updates_made.append(f"Mfr: {metadata['manufacturer']}")
                if metadata and metadata.get('operator'):
                    updates_made.append(f"Op: {metadata['operator']}")
                if routes and (routes.get('origin') or routes.get('destination')):
                    origin = routes.get('origin') or '?'
                    dest = routes.get('destination') or '?'
                    updates_made.append(f"Route: {origin}→{dest}")

                print(f"  ✓ Updated: {', '.join(updates_made)}")
                updated_count += 1
            else:
                print(f"  ○ No new data")
        else:
            print(f"  ✗ No data available")
            failed_count += 1

        # Rate limiting - OpenSky has limits
        if idx < total:
            time.sleep(2)  # 2 seconds between aircraft

    conn.close()

    print()
    print("=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✓ Updated with new data:  {updated_count}")
    print(f"  ✗ No data found:          {failed_count}")
    print(f"  Total processed:          {total}")
    print()
    print("Database updated! Refresh http://localhost:8080/stats.html")
    print()

if __name__ == "__main__":
    try:
        backfill_enhanced()
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
        print("Partial updates have been saved to the database.")
