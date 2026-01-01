#!/usr/bin/env python3
"""
Coverage Analyzer - Analyze antenna coverage and find blind spots
Shows reception patterns by direction, distance, and altitude
"""

import sqlite3
import math
from collections import defaultdict

DATABASE = 'flight_log.db'

def get_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2"""
    dlon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    y = math.sin(dlon) * math.cos(lat2)
    x = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def direction_name(bearing):
    """Convert bearing to cardinal direction"""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = int((bearing + 11.25) / 22.5) % 16
    return directions[index]

def analyze_coverage():
    """Analyze antenna coverage from position data"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get your antenna location from a sample position
    cursor.execute('''
        SELECT AVG(latitude), AVG(longitude)
        FROM signal_quality
        WHERE latitude IS NOT NULL
        LIMIT 1
    ''')

    # Get all position data
    cursor.execute('''
        SELECT
            icao,
            latitude,
            longitude,
            altitude,
            distance,
            rssi,
            callsign
        FROM signal_quality
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp
    ''')

    positions = cursor.fetchall()

    if not positions:
        print("No position data found!")
        print("Make sure position_tracker.py is running.")
        return

    print("=" * 80)
    print("  ANTENNA COVERAGE ANALYSIS")
    print("=" * 80)
    print()

    # Assume antenna is at center of reception area
    lats = [p[1] for p in positions]
    lons = [p[2] for p in positions]
    antenna_lat = sum(lats) / len(lats)
    antenna_lon = sum(lons) / len(lons)

    print(f"Estimated Antenna Location: {antenna_lat:.4f}°, {antenna_lon:.4f}°")
    print(f"Total Position Updates: {len(positions)}")
    print()

    # Analyze by direction
    direction_stats = defaultdict(lambda: {'count': 0, 'max_distance': 0, 'avg_rssi': []})

    for pos in positions:
        icao, lat, lon, alt, dist, rssi, callsign = pos

        # Calculate bearing
        bearing = get_bearing(antenna_lat, antenna_lon, lat, lon)
        direction = direction_name(bearing)

        direction_stats[direction]['count'] += 1
        direction_stats[direction]['max_distance'] = max(
            direction_stats[direction]['max_distance'],
            dist or 0
        )
        if rssi:
            direction_stats[direction]['avg_rssi'].append(rssi)

    # Print direction analysis
    print("=" * 80)
    print("  COVERAGE BY DIRECTION")
    print("=" * 80)
    print(f"{'Direction':<10} {'Updates':<10} {'Max Range (km)':<15} {'Avg RSSI (dBFS)':<15}")
    print("-" * 80)

    directions_ordered = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                          'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    for direction in directions_ordered:
        if direction in direction_stats:
            stats = direction_stats[direction]
            avg_rssi = sum(stats['avg_rssi']) / len(stats['avg_rssi']) if stats['avg_rssi'] else 0
            print(f"{direction:<10} {stats['count']:<10} "
                  f"{stats['max_distance']:<15.1f} {avg_rssi:<15.1f}")

    print()

    # Analyze by distance
    print("=" * 80)
    print("  COVERAGE BY DISTANCE")
    print("=" * 80)

    distance_ranges = [
        (0, 50, '0-50 km'),
        (50, 100, '50-100 km'),
        (100, 150, '100-150 km'),
        (150, 200, '150-200 km'),
        (200, 300, '200-300 km'),
        (300, 500, '300+ km')
    ]

    print(f"{'Range':<15} {'Updates':<10} {'Avg RSSI (dBFS)':<15}")
    print("-" * 80)

    for min_dist, max_dist, label in distance_ranges:
        range_positions = [p for p in positions if p[4] and min_dist <= p[4] < max_dist]
        count = len(range_positions)
        rssi_values = [p[5] for p in range_positions if p[5]]
        avg_rssi = sum(rssi_values) / len(rssi_values) if rssi_values else 0

        print(f"{label:<15} {count:<10} {avg_rssi:<15.1f}")

    print()

    # Analyze by altitude
    print("=" * 80)
    print("  COVERAGE BY ALTITUDE")
    print("=" * 80)

    altitude_ranges = [
        (0, 5000, '0-5,000 ft'),
        (5000, 10000, '5,000-10,000 ft'),
        (10000, 20000, '10,000-20,000 ft'),
        (20000, 30000, '20,000-30,000 ft'),
        (30000, 40000, '30,000-40,000 ft'),
        (40000, 50000, '40,000+ ft')
    ]

    print(f"{'Altitude':<20} {'Updates':<10} {'Avg Distance (km)':<15}")
    print("-" * 80)

    for min_alt, max_alt, label in altitude_ranges:
        range_positions = [p for p in positions if p[3] and min_alt <= p[3] < max_alt]
        count = len(range_positions)
        distances = [p[4] for p in range_positions if p[4]]
        avg_dist = sum(distances) / len(distances) if distances else 0

        print(f"{label:<20} {count:<10} {avg_dist:<15.1f}")

    print()

    # Find blind spots (directions with low coverage)
    print("=" * 80)
    print("  POTENTIAL BLIND SPOTS")
    print("=" * 80)

    avg_coverage = sum(s['count'] for s in direction_stats.values()) / len(direction_stats)

    blind_spots = []
    for direction in directions_ordered:
        if direction not in direction_stats:
            blind_spots.append((direction, 0))
        elif direction_stats[direction]['count'] < avg_coverage * 0.3:
            blind_spots.append((direction, direction_stats[direction]['count']))

    if blind_spots:
        print("Directions with low coverage (< 30% of average):")
        for direction, count in blind_spots:
            print(f"  - {direction}: {count} updates")
    else:
        print("No significant blind spots detected!")

    print()
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    analyze_coverage()
