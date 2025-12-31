#!/usr/bin/env python3
"""Test ICAO to IATA callsign conversion and route lookup"""

import os
import requests

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

# Test callsigns from your flights
test_callsigns = ['ASA7004', 'WJA290', 'WEN3715', 'FLE1877']
api_key = '3e3ae5e788673f961d6d0049899416c1'

print("=" * 70)
print("TESTING CALLSIGN CONVERSION AND ROUTE LOOKUP")
print("=" * 70)
print()

for icao_callsign in test_callsigns:
    iata_callsign = convert_icao_to_iata_callsign(icao_callsign)

    print(f"ICAO: {icao_callsign} → IATA: {iata_callsign}")

    try:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': api_key,
            'flight_iata': iata_callsign
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                flight = data['data'][0]
                departure = flight.get('departure', {})
                arrival = flight.get('arrival', {})

                origin = departure.get('iata') or departure.get('icao') or '?'
                dest = arrival.get('iata') or arrival.get('icao') or '?'

                print(f"  ✓ Route: {origin} → {dest}")
                print(f"    From: {departure.get('airport', 'Unknown')}")
                print(f"    To: {arrival.get('airport', 'Unknown')}")
            else:
                print(f"  ✗ No route data (API returned 0 flights)")
        else:
            print(f"  ✗ API error: {response.status_code}")

    except Exception as e:
        print(f"  ✗ Exception: {e}")

    print()

print("=" * 70)
