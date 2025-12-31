#!/usr/bin/env python3
"""Test route API calls directly"""

import os
import requests

# Test callsigns from your recent flights
test_callsigns = ['ASA7004', 'WJA290', 'WEN3715', 'FLE1877']

api_key = '3e3ae5e788673f961d6d0049899416c1'

print("=" * 70)
print("TESTING AVIATION STACK API ROUTE LOOKUPS")
print("=" * 70)
print()

for callsign in test_callsigns:
    print(f"Testing callsign: {callsign}")
    print(f"  Trying IATA format: {callsign}")

    try:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': api_key,
            'flight_iata': callsign.strip()
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"  Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Data found: {len(data.get('data', []))} flights")

            if data.get('data') and len(data['data']) > 0:
                flight = data['data'][0]
                departure = flight.get('departure', {})
                arrival = flight.get('arrival', {})

                origin = departure.get('iata') or departure.get('icao')
                dest = arrival.get('iata') or arrival.get('icao')

                print(f"  ✓ Route found: {origin} → {dest}")
                print(f"    Departure: {departure.get('airport', 'Unknown')}")
                print(f"    Arrival: {arrival.get('airport', 'Unknown')}")
            else:
                print(f"  ✗ No flight data returned")
                if 'error' in data:
                    print(f"  Error: {data['error']}")
        else:
            print(f"  ✗ HTTP error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ✗ Exception: {e}")

    print()

print("=" * 70)
print("NOTE: Aviation Stack API uses IATA callsigns, not ICAO.")
print("ICAO callsigns like 'WJA290' need to be converted to IATA format.")
print("Example: WJA = WS (WestJet IATA code)")
print("=" * 70)
