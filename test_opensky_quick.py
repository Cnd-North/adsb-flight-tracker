#!/usr/bin/env python3
"""Quick test of OpenSky APIs"""

import requests
import time

# Test 1: Aircraft metadata
print("Test 1: Aircraft Metadata API")
print("-" * 40)
icao = "c07f02"
url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao}"
response = requests.get(url, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Registration: {data.get('registration')}")
    print(f"Manufacturer: {data.get('manufacturerName')}")
    print(f"Model: {data.get('model')}")
    print(f"Operator: {data.get('operator')}")
print()

time.sleep(2)

# Test 2: Flights API for routes
print("Test 2: Flights API (Routes)")
print("-" * 40)
import time as t
from datetime import datetime, timedelta

now = datetime.now()
begin = int((now - timedelta(days=7)).timestamp())
end = int(now.timestamp())

url = f"https://opensky-network.org/api/flights/aircraft"
params = {'icao24': icao, 'begin': begin, 'end': end}
response = requests.get(url, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Flights found: {len(data) if data else 0}")
    if data and len(data) > 0:
        flight = data[0]
        print(f"Origin: {flight.get('estDepartureAirport')}")
        print(f"Destination: {flight.get('estArrivalAirport')}")
print()

print("Tests complete!")
