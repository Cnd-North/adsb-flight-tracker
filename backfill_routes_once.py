#!/usr/bin/env python3
"""One-time backfill of routes for flights with callsigns but no route data"""

import sqlite3
import os
import requests
import time
import api_quota_manager as quota

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")
API_KEY = os.getenv('AVIATIONSTACK_KEY', '')

# ICAO to IATA mapping
ICAO_TO_IATA = {
    'ACA': 'AC',   # Air Canada
    'WJA': 'WS',   # WestJet
    'WEN': 'WS',   # WestJet Encore
    'UAL': 'UA',   # United
    'DAL': 'DL',   # Delta
    'AAL': 'AA',   # American
    'ASA': 'AS',   # Alaska
    'JBU': 'B6',   # JetBlue
    'SWA': 'WN',   # Southwest
    'FFT': 'F9',   # Frontier
    'FLE': 'F8',   # Flair Airlines
    'SKW': 'OO',   # SkyWest
    'RPA': 'YX',   # Republic Airways
    'ENY': 'MQ',   # Envoy Air
    'PDT': 'OH',   # Piedmont Airlines
    'CPZ': 'CP',   # Compass Airlines
    'AMX': 'AM',   # Aeromexico
    'JZA': 'JZ',   # Skyways (placeholder, may not be accurate)
}

def convert_icao_to_iata_callsign(callsign):
    """Convert ICAO callsign to IATA format"""
    if not callsign or len(callsign) < 3:
        return callsign

    airline_icao = callsign[:3].upper()
    flight_number = callsign[3:].strip()

    airline_iata = ICAO_TO_IATA.get(airline_icao)

    if airline_iata:
        return f"{airline_iata}{flight_number}"

    return callsign

def get_route_from_api(callsign):
    """Get route from Aviation Stack API"""
    # Check quota
    can_request, status_msg = quota.can_make_request('aviationstack', callsign)
    if not can_request:
        print(f"  ⚠️  {status_msg}")
        return None

    # Convert to IATA
    iata_callsign = convert_icao_to_iata_callsign(callsign)

    try:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': API_KEY,
            'flight_iata': iata_callsign.strip()
        }

        response = requests.get(url, params=params, timeout=5)

        # Record request
        remaining = quota.record_request('aviationstack')

        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                flight = data['data'][0]
                departure = flight.get('departure', {})
                arrival = flight.get('arrival', {})

                origin = departure.get('iata') or departure.get('icao')
                dest = arrival.get('iata') or arrival.get('icao')

                if origin or dest:
                    return {
                        'origin': origin,
                        'destination': dest
                    }

        return None

    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return None

def main():
    print("=" * 70)
    print("ONE-TIME ROUTE BACKFILL FOR HISTORICAL FLIGHTS")
    print("=" * 70)
    print()

    # Show initial quota
    status = quota.get_quota_status()
    remaining = status['apis']['aviationstack']['remaining']
    print(f"Initial quota: {remaining} requests remaining")
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find flights with callsigns but no routes
    cursor.execute('''
        SELECT DISTINCT icao, callsign
        FROM flights
        WHERE callsign IS NOT NULL
        AND (origin_airport IS NULL OR origin_airport = '')
        AND (destination_airport IS NULL OR destination_airport = '')
        ORDER BY first_seen DESC
    ''')

    flights_to_backfill = cursor.fetchall()

    print(f"Found {len(flights_to_backfill)} flights with callsigns but no routes")
    print()

    if len(flights_to_backfill) == 0:
        print("✓ All flights already have route data!")
        conn.close()
        return

    updated = 0
    skipped = 0

    for icao, callsign in flights_to_backfill:
        print(f"Processing {callsign} ({icao})...")

        route = get_route_from_api(callsign)

        if route:
            # Update the flight with route data
            cursor.execute('''
                UPDATE flights
                SET origin_airport = ?,
                    destination_airport = ?
                WHERE callsign = ? AND icao = ?
            ''', (
                route['origin'],
                route['destination'],
                callsign,
                icao
            ))

            conn.commit()
            updated += 1

            origin = route.get('origin') or '?'
            dest = route.get('destination') or '?'
            print(f"  ✓ Updated: {origin} → {dest}")
        else:
            skipped += 1
            print(f"  ○ No route data available")

        # Small delay to avoid rate limiting
        time.sleep(0.5)

        print()

    conn.close()

    print("=" * 70)
    print(f"BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Flights updated with routes: {updated}")
    print(f"Flights skipped (no data): {skipped}")

    # Show final quota
    status = quota.get_quota_status()
    remaining = status['apis']['aviationstack']['remaining']
    used = status['apis']['aviationstack']['used']
    print(f"\nFinal quota: {remaining} requests remaining ({used} used this month)")
    print("=" * 70)

if __name__ == "__main__":
    main()
