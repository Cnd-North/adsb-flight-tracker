#!/usr/bin/env python3
"""
Fetch Flight Routes
Gets origin/destination airports for flights using FlightAware API
"""

import sqlite3
import requests
import time
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

# FlightAware API Configuration
# Get your free API key from: https://flightaware.com/commercial/aeroapi/
FLIGHTAWARE_API_KEY = os.getenv('FLIGHTAWARE_API_KEY', '')

def get_route_from_flightaware(callsign):
    """Get route information from FlightAware AeroAPI"""
    if not FLIGHTAWARE_API_KEY:
        return None

    try:
        # Remove whitespace from callsign
        callsign = callsign.strip()

        # FlightAware AeroAPI endpoint
        url = f"https://aeroapi.flightaware.com/aeroapi/flights/{callsign}"
        headers = {"x-apikey": FLIGHTAWARE_API_KEY}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('flights') and len(data['flights']) > 0:
                flight = data['flights'][0]
                return {
                    'origin': flight.get('origin', {}).get('code'),
                    'destination': flight.get('destination', {}).get('code'),
                }

        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def get_route_from_adsbexchange(callsign):
    """Try to get route from ADS-B Exchange (free, but limited)"""
    try:
        # This is a simplified approach - ADSB Exchange API also requires key
        # But you can use their public data
        print(f"  Note: ADS-B Exchange requires API key for route data")
        return None
    except:
        return None

def backfill_routes():
    """Update all flights with missing route data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find flights with callsigns but no route data
    cursor.execute('''
        SELECT DISTINCT callsign, icao
        FROM flights
        WHERE callsign IS NOT NULL
        AND callsign != ''
        AND (origin_airport IS NULL OR destination_airport IS NULL)
        ORDER BY first_seen DESC
    ''')

    flights_to_update = cursor.fetchall()
    total = len(flights_to_update)

    print("=" * 80)
    print("FLIGHT ROUTE BACKFILL")
    print("=" * 80)

    if not FLIGHTAWARE_API_KEY:
        print("\n⚠️  WARNING: No FlightAware API key found!")
        print("\nTo enable route lookup:")
        print("1. Sign up for free at: https://flightaware.com/commercial/aeroapi/")
        print("2. Get your API key")
        print("3. Run: export FLIGHTAWARE_API_KEY='your-key-here'")
        print("4. Then run this script again")
        print("\nFree tier includes: 10,000 queries/month, 2 queries/minute")
        print("=" * 80)
        return

    print(f"\nFound {total} flights to update")
    print("\nStarting route backfill...")
    print("=" * 80)
    print()

    updated_count = 0
    failed_count = 0

    for idx, (callsign, icao) in enumerate(flights_to_update, 1):
        print(f"[{idx}/{total}] {callsign} ({icao})...", end=" ")

        # Try FlightAware
        route = get_route_from_flightaware(callsign)

        if route and (route.get('origin') or route.get('destination')):
            cursor.execute('''
                UPDATE flights
                SET origin_airport = COALESCE(origin_airport, ?),
                    destination_airport = COALESCE(destination_airport, ?)
                WHERE callsign = ?
            ''', (
                route.get('origin'),
                route.get('destination'),
                callsign
            ))

            conn.commit()

            origin = route.get('origin') or '?'
            dest = route.get('destination') or '?'
            print(f"✓ {origin} → {dest}")
            updated_count += 1

        else:
            print("✗ No route data")
            failed_count += 1

        # Rate limiting for FlightAware free tier (2 requests/minute)
        if idx < total:
            time.sleep(30)  # Wait 30 seconds between requests

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

def show_route_examples():
    """Show some example routes from the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT callsign, registration, origin_airport, destination_airport
        FROM flights
        WHERE origin_airport IS NOT NULL OR destination_airport IS NOT NULL
        ORDER BY first_seen DESC
        LIMIT 10
    ''')

    results = cursor.fetchall()
    conn.close()

    if results:
        print("\nExample routes in database:")
        print("-" * 60)
        for callsign, reg, origin, dest in results:
            origin = origin or '?'
            dest = dest or '?'
            print(f"  {callsign:10} {reg:10} {origin} → {dest}")
    else:
        print("\nNo routes in database yet.")

if __name__ == "__main__":
    try:
        backfill_routes()
        show_route_examples()
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
