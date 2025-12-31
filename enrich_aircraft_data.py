#!/usr/bin/env python3
"""
ADS-B Data Enrichment Service
Reads dump1090 aircraft.json, enriches with OpenSky data, and creates enhanced JSON
"""

import json
import requests
import time
import os
from datetime import datetime

# Configuration
INPUT_JSON = os.path.expanduser("~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft.json")
OUTPUT_JSON = os.path.expanduser("~/radioconda/Projects/dump1090-fa-web/public_html/data/aircraft_enriched.json")
OPENSKY_API = "https://opensky-network.org/api/states/all"
UPDATE_INTERVAL = 15  # seconds between updates
CACHE_DURATION = 300  # Cache API results for 5 minutes

# Cache for API results
api_cache = {}
stats = {
    'total_queries': 0,
    'cache_hits': 0,
    'api_calls': 0,
    'errors': 0
}

def get_opensky_data(icao24):
    """Query OpenSky Network API for aircraft info with caching"""
    global stats

    # Check cache first
    if icao24 in api_cache:
        cached_time, cached_data = api_cache[icao24]
        if time.time() - cached_time < CACHE_DURATION:
            stats['cache_hits'] += 1
            return cached_data

    stats['total_queries'] += 1

    try:
        # Query OpenSky Network
        url = f"{OPENSKY_API}?icao24={icao24.lower()}"
        response = requests.get(url, timeout=5)
        stats['api_calls'] += 1

        if response.status_code == 200:
            data = response.json()

            if data.get('states') and len(data['states']) > 0:
                state = data['states'][0]
                info = {
                    'origin_country': state[2],
                    'on_ground': state[8],
                }
                # Cache the result
                api_cache[icao24] = (time.time(), info)
                return info

        return None

    except Exception as e:
        stats['errors'] += 1
        print(f"Error querying OpenSky for {icao24}: {e}")
        return None

def enrich_aircraft_data():
    """Read dump1090 data, enrich it, and write enhanced JSON"""
    try:
        # Read original data
        with open(INPUT_JSON, 'r') as f:
            data = json.load(f)

        aircraft_list = data.get('aircraft', [])

        # Enrich each aircraft
        enriched_aircraft = []
        for aircraft in aircraft_list:
            icao = aircraft.get('hex', '').lower()
            enriched = aircraft.copy()

            # Only query for aircraft with good signal (more than 10 messages)
            if aircraft.get('messages', 0) > 10 and icao:
                opensky_data = get_opensky_data(icao)
                if opensky_data:
                    enriched['country'] = opensky_data.get('origin_country', 'Unknown')
                    enriched['on_ground'] = opensky_data.get('on_ground', False)

            enriched_aircraft.append(enriched)

        # Create enriched output
        enriched_data = {
            'now': data.get('now'),
            'messages': data.get('messages'),
            'aircraft': enriched_aircraft,
            'enrichment_stats': {
                'total_aircraft': len(aircraft_list),
                'enriched_aircraft': len([a for a in enriched_aircraft if 'country' in a]),
                'cache_size': len(api_cache),
                'total_queries': stats['total_queries'],
                'cache_hits': stats['cache_hits'],
                'api_calls': stats['api_calls'],
                'errors': stats['errors'],
                'last_update': datetime.now().isoformat()
            }
        }

        # Write enriched data
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(enriched_data, f, indent=2)

        return len(aircraft_list), len([a for a in enriched_aircraft if 'country' in a])

    except Exception as e:
        print(f"Error enriching data: {e}")
        return 0, 0

def main():
    """Main loop"""
    print("=" * 80)
    print("ADS-B Data Enrichment Service")
    print("=" * 80)
    print(f"Input:  {INPUT_JSON}")
    print(f"Output: {OUTPUT_JSON}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"OpenSky API cache: {CACHE_DURATION} seconds")
    print("=" * 80)
    print()
    print("Starting enrichment service... (Press Ctrl+C to stop)")
    print()

    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            total, enriched = enrich_aircraft_data()

            print(f"[{timestamp}] Iteration {iteration}: {total} aircraft, {enriched} enriched | "
                  f"Cache: {len(api_cache)} | API calls: {stats['api_calls']} | "
                  f"Cache hits: {stats['cache_hits']} | Errors: {stats['errors']}")

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n")
        print("=" * 80)
        print("Shutting down enrichment service")
        print("=" * 80)
        print(f"Total queries: {stats['total_queries']}")
        print(f"API calls: {stats['api_calls']}")
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Errors: {stats['errors']}")
        print(f"Final cache size: {len(api_cache)} aircraft")
        print()

if __name__ == "__main__":
    main()
