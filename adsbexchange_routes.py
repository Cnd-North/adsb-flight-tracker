#!/usr/bin/env python3
"""
ADS-B Exchange Route Backfill
Uses ADS-B Exchange public API v2 to fetch route information
Free tier: No API key needed for basic queries
"""

import sqlite3
import requests
import time
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

def get_adsbx_routes(icao):
    """Get route from ADS-B Exchange v2 API"""
    try:
        # ADS-B Exchange v2 API endpoint
        # This is their public API - rate limited but free
        url = f"https://globe.adsbexchange.com/globe_history/2024/12/30/{icao.lower()}.json"

        # Try current data endpoint
        headers = {
            'User-Agent': 'Mozilla/5.0 (flight logger script)'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # ADSB Exchange format varies
            # Try to extract route info if available
            if 'trace' in data:
                # Historical trace data
                return None  # This endpoint doesn't have route info

        # Try their aircraft database endpoint
        url2 = f"https://api.adsbexchange.com/v2/icao/{icao.lower()}/"
        response2 = requests.get(url2, headers=headers, timeout=10)

        if response2.status_code == 200:
            data2 = response2.json()
            if 'ac' in data2 and len(data2['ac']) > 0:
                aircraft = data2['ac'][0]
                # Check for flight/route info
                flight = aircraft.get('flight', '').strip()
                # Route not typically in free tier
                return None

    except Exception as e:
        pass

    return None

def try_aviationstack(callsign):
    """Try Aviation Stack API (requires free API key)"""
    # Free tier: 100 requests/month
    # Sign up at: https://aviationstack.com/
    api_key = os.getenv('AVIATIONSTACK_KEY', '')

    if not api_key:
        return None

    try:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': api_key,
            'flight_iata': callsign
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                flight = data['data'][0]
                departure = flight.get('departure', {})
                arrival = flight.get('arrival', {})

                return {
                    'origin': departure.get('iata'),
                    'destination': arrival.get('iata')
                }
    except Exception as e:
        pass

    return None

def backfill_routes():
    """Backfill route data from available APIs"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get flights missing route data with callsigns
    cursor.execute('''
        SELECT DISTINCT icao, callsign
        FROM flights
        WHERE (origin_airport IS NULL OR destination_airport IS NULL)
        AND callsign IS NOT NULL
        AND callsign != ''
        ORDER BY first_seen DESC
    ''')

    flights_to_update = cursor.fetchall()
    total = len(flights_to_update)

    print("=" * 80)
    print("ROUTE DATA BACKFILL")
    print("=" * 80)
    print(f"\nFound {total} flights with callsigns but no route data")
    print("\nChecking free APIs for route information...")
    print("=" * 80)

    # Check for API keys
    has_aviationstack = bool(os.getenv('AVIATIONSTACK_KEY'))

    if not has_aviationstack:
        print("\n💡 Tip: For better route data, sign up for free APIs:")
        print("   - Aviation Stack: https://aviationstack.com/ (100 requests/month)")
        print("   - Set key: export AVIATIONSTACK_KEY='your-key'")
        print()

    print("Starting route lookup...")
    print("=" * 80)
    print()

    updated_count = 0
    failed_count = 0

    for idx, (icao, callsign) in enumerate(flights_to_update, 1):
        print(f"[{idx}/{total}] {callsign} ({icao})...", end=" ")

        routes = None

        # Try Aviation Stack if key available
        if has_aviationstack:
            routes = try_aviationstack(callsign)
            time.sleep(1)

        # Try other free sources here...
        # (Most free APIs don't provide historical route data)

        if routes and (routes.get('origin') or routes.get('destination')):
            cursor.execute('''
                UPDATE flights
                SET origin_airport = COALESCE(origin_airport, ?),
                    destination_airport = COALESCE(destination_airport, ?)
                WHERE icao = ? AND callsign = ?
            ''', (
                routes.get('origin'),
                routes.get('destination'),
                icao,
                callsign
            ))

            conn.commit()

            origin = routes.get('origin') or '?'
            dest = routes.get('destination') or '?'
            print(f"✓ {origin} → {dest}")
            updated_count += 1
        else:
            print("✗ No route data available")
            failed_count += 1

        time.sleep(2)  # Rate limiting

    conn.close()

    print()
    print("=" * 80)
    print("ROUTE BACKFILL COMPLETE")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✓ Successfully updated: {updated_count}")
    print(f"  ✗ No data found:        {failed_count}")
    print(f"  Total processed:        {total}")
    print()

    if updated_count == 0:
        print("⚠️  ROUTE DATA LIMITATION:")
        print()
        print("Free APIs typically DON'T provide historical route data.")
        print("Most free APIs only show CURRENT/LIVE flights, not past flights.")
        print()
        print("Options for route data:")
        print("  1. FlightAware (Paid) - Most comprehensive historical data")
        print("  2. Aviation Stack (Free tier very limited)")
        print("  3. Only track LIVE flights going forward (no backfill)")
        print()
        print("✨ The enhanced logger now captures routes for NEW flights automatically!")
        print()

if __name__ == "__main__":
    try:
        backfill_routes()
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
