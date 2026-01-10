#!/usr/bin/env python3
"""
Calculate antenna location and height from position data
Uses triangulation and signal analysis
"""

import sqlite3
import math
from collections import defaultdict

DATABASE = 'flight_log.db'

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_antenna_location():
    """Calculate antenna location from position data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get all positions with signal strength
    cursor.execute('''
        SELECT latitude, longitude, altitude, distance, rssi
        FROM signal_quality
        WHERE latitude IS NOT NULL
        AND longitude IS NOT NULL
        AND rssi IS NOT NULL
        ORDER BY rssi DESC
    ''')

    positions = cursor.fetchall()
    conn.close()

    if len(positions) < 3:
        return None

    # Weight positions by signal strength (inverse of RSSI - closer to 0 is stronger)
    weighted_lat = 0
    weighted_lon = 0
    total_weight = 0

    # Use the strongest signals (assume they're closest)
    strongest_positions = sorted(positions, key=lambda x: x[4], reverse=True)[:20]

    for lat, lon, alt, dist, rssi in strongest_positions:
        # Weight by signal strength (normalize RSSI)
        # Strong signals are closer to 0, weak signals are more negative
        weight = 1.0 / (abs(rssi) + 1)
        weighted_lat += lat * weight
        weighted_lon += lon * weight
        total_weight += weight

    if total_weight == 0:
        return None

    antenna_lat = weighted_lat / total_weight
    antenna_lon = weighted_lon / total_weight

    # Estimate antenna height
    # Find closest aircraft positions (strongest signals)
    closest_with_altitude = [p for p in strongest_positions if p[2] and p[3]]

    if closest_with_altitude:
        # Calculate antenna height based on line of sight to closest aircraft
        # Assuming clear line of sight, antenna is at ground level of closest receptions
        heights = []
        for lat, lon, alt, dist, rssi in closest_with_altitude[:10]:
            # Calculate elevation angle (very rough estimate)
            # altitude is in feet, distance is in km
            alt_m = alt * 0.3048  # feet to meters
            dist_m = dist * 1000  # km to meters

            if dist_m > 0:
                # Line of sight: height = altitude - (distance * tan(elevation_angle))
                # For now, assume antenna is at average local ground level
                # We can estimate this from the lowest altitude aircraft at close range
                heights.append(alt_m - dist_m * 0.1)  # Rough approximation

        antenna_height_m = max(0, sum(heights) / len(heights)) if heights else 0
        antenna_height_ft = antenna_height_m * 3.28084  # meters to feet
    else:
        antenna_height_ft = 0

    # Calculate actual distance from estimated location to verify
    distances = []
    for lat, lon, alt, dist, rssi in strongest_positions:
        actual_dist = haversine_distance(antenna_lat, antenna_lon, lat, lon)
        distances.append(actual_dist)

    avg_distance = sum(distances) / len(distances) if distances else 0

    return {
        'latitude': antenna_lat,
        'longitude': antenna_lon,
        'height_meters': antenna_height_m if 'antenna_height_m' in locals() else 0,
        'height_feet': antenna_height_ft if 'antenna_height_ft' in locals() else 0,
        'confidence': 'high' if len(strongest_positions) > 10 else 'medium' if len(strongest_positions) > 5 else 'low',
        'samples': len(positions),
        'avg_distance_km': avg_distance
    }

if __name__ == "__main__":
    result = calculate_antenna_location()
    if result:
        print(f"Antenna Location: {result['latitude']:.6f}°, {result['longitude']:.6f}°")
        print(f"Estimated Height: {result['height_feet']:.0f} ft ({result['height_meters']:.0f} m)")
        print(f"Confidence: {result['confidence']}")
        print(f"Based on {result['samples']} position samples")
    else:
        print("Not enough data to calculate antenna location")
