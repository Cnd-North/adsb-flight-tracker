#!/usr/bin/env python3
"""
Intelligent Route API Optimizer
Prioritizes unique/interesting flights over common commercial routes
"""

import sqlite3
import os
import re
from datetime import datetime, timedelta

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

# Military callsign patterns
MILITARY_PATTERNS = [
    r'^RCH\d+',      # Reach (USAF)
    r'^CNV\d+',      # Convoy (USAF)
    r'^EVAC\d+',     # Evacuation
    r'^SPAR\d+',     # Special Air Resources
    r'^DUKE\d+',     # Duke (VIP)
    r'^VM\d+',       # Marine aircraft
    r'^NAVY\d+',     # Navy aircraft
    r'^ARMY\d+',     # Army aircraft
    r'^COAST\d+',    # Coast Guard
    r'^GUARD\d+',    # Coast Guard
    r'^CFC\d+',      # Canadian Forces
    r'^CANFORCE\d+', # Canadian Forces
    r'^RAF\d+',      # Royal Air Force
    r'^ASCOT\d+',    # RAF transport
    r'^RAFAIR\d+',   # RAF
]

# Cargo airline ICAO codes
CARGO_AIRLINES = {
    'FDX': 'FedEx',
    'UPS': 'UPS',
    'GTI': 'Atlas Air',
    'ABX': 'ABX Air',
    'ATN': 'Air Transport International',
    'KFS': 'Kalitta Air',
    'NCR': 'National Airlines',
    'PAC': 'Polar Air Cargo',
    'SWN': 'Southern Air',
    'CKS': 'Kalitta Charters',
    'WES': 'Western Global',
    'CAO': 'Air China Cargo',
    'CPA': 'Cathay Pacific Cargo',
    'CLX': 'Cargolux',
    'MPH': 'Martinair Cargo',
}

# Very common commercial routes to deprioritize (after seen once)
COMMON_ROUTES = {
    # Major US transcontinental
    ('LAX', 'JFK'), ('JFK', 'LAX'),
    ('SFO', 'JFK'), ('JFK', 'SFO'),
    ('LAX', 'EWR'), ('EWR', 'LAX'),
    ('ORD', 'LAX'), ('LAX', 'ORD'),

    # Major US domestic
    ('ATL', 'LAX'), ('LAX', 'ATL'),
    ('DFW', 'LAX'), ('LAX', 'DFW'),
    ('DEN', 'LAX'), ('LAX', 'DEN'),
    ('SEA', 'LAX'), ('LAX', 'SEA'),
    ('PHX', 'LAX'), ('LAX', 'PHX'),

    # Canadian major routes
    ('YVR', 'YYZ'), ('YYZ', 'YVR'),
    ('YVR', 'YYC'), ('YYC', 'YVR'),
    ('YYZ', 'YUL'), ('YUL', 'YYZ'),
}

def is_military(callsign):
    """Check if callsign appears to be military"""
    if not callsign:
        return False

    callsign = callsign.upper().strip()

    for pattern in MILITARY_PATTERNS:
        if re.match(pattern, callsign):
            return True

    return False

def is_cargo(callsign):
    """Check if callsign is from a cargo airline"""
    if not callsign or len(callsign) < 3:
        return False

    # Extract airline code (first 3 letters)
    airline_code = callsign[:3].upper()

    return airline_code in CARGO_AIRLINES

def is_private(callsign, registration=None):
    """Check if flight is private/general aviation"""
    if not callsign:
        return False

    callsign = callsign.upper().strip()

    # Private aircraft often use registration as callsign
    # N-numbers, C-numbers, etc.
    if registration and callsign == registration.replace('-', '').upper():
        return True

    # Single letter followed by numbers (like N12345)
    if re.match(r'^[A-Z]\d+[A-Z]*$', callsign):
        return True

    # Registration patterns without dashes
    if re.match(r'^(N|C|G|D|F)[A-Z0-9]+$', callsign):
        return True

    return False

def get_route_commonality(origin, dest):
    """Check how common a route is (higher = more common)"""
    if not origin or not dest:
        return 0

    route = (origin, dest)

    # Check if it's a known common route
    if route in COMMON_ROUTES:
        # Check how many times we've seen this route
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM flights
            WHERE origin_airport = ? AND destination_airport = ?
        ''', (origin, dest))

        count = cursor.fetchone()[0]
        conn.close()

        # If we've seen this common route multiple times, deprioritize heavily
        if count >= 3:
            return 100  # Very common, skip
        elif count >= 1:
            return 50   # Seen before, low priority
        else:
            return 25   # Common route but not logged yet

    return 0  # Unknown route, interesting!

def is_unique_destination(airport):
    """Check if this airport is rare/unique"""
    if not airport:
        return False

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if we've ever seen this airport
    cursor.execute('''
        SELECT COUNT(*) FROM flights
        WHERE origin_airport = ? OR destination_airport = ?
    ''', (airport, airport))

    count = cursor.fetchone()[0]
    conn.close()

    return count == 0  # Never seen before = unique!

def calculate_priority_score(callsign, icao, registration=None):
    """
    Calculate priority score for API call (higher = more interesting)

    Score factors:
    - Military: +100
    - Private/General Aviation: +80
    - Cargo: +60
    - Unique destination: +50
    - Common route (seen before): -50 to -100
    - Commercial scheduled: +20 (baseline)
    """

    if not callsign:
        return 0

    score = 20  # Baseline for commercial
    reasons = []

    # Check flight type
    if is_military(callsign):
        score += 100
        reasons.append("MILITARY")

    if is_private(callsign, registration):
        score += 80
        reasons.append("PRIVATE")

    if is_cargo(callsign):
        score += 60
        reasons.append("CARGO")

    # Check if we've already logged this exact callsign recently
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check for duplicate in last 7 days
    cursor.execute('''
        SELECT origin_airport, destination_airport, COUNT(*) as count
        FROM flights
        WHERE callsign = ? AND first_seen >= datetime('now', '-7 days')
        GROUP BY origin_airport, destination_airport
        ORDER BY count DESC
        LIMIT 1
    ''', (callsign,))

    recent = cursor.fetchone()

    if recent:
        origin, dest, count = recent

        if origin and dest:
            # We have the route for this callsign already
            commonality = get_route_commonality(origin, dest)

            if commonality >= 100:
                score -= 100
                reasons.append(f"VERY_COMMON({origin}-{dest}, seen {count}x)")
            elif commonality >= 50:
                score -= 50
                reasons.append(f"COMMON({origin}-{dest}, seen {count}x)")
            elif count >= 3:
                score -= 30
                reasons.append(f"REPEAT({origin}-{dest}, {count}x)")

    conn.close()

    # Bonus for unique features
    if score > 0:
        # Check if this ICAO is from a rare country
        if icao and len(icao) >= 6:
            # Check country allocation
            first_byte = icao[:2].upper()

            # Non-US/Canada aircraft get bonus (more interesting internationally)
            if first_byte not in ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7',  # USA
                                  'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']:  # Canada
                score += 30
                reasons.append("INTERNATIONAL")

    return score, reasons

def should_call_api(callsign, icao, registration=None, quota_remaining=0):
    """
    Determine if we should make an API call for this flight

    Returns: (should_call: bool, score: int, reason: str)
    """

    score, reasons = calculate_priority_score(callsign, icao, registration)

    # Decision thresholds based on remaining quota
    if quota_remaining > 50:
        # Plenty of quota, be generous
        threshold = 20
    elif quota_remaining > 20:
        # Getting low, prioritize interesting flights
        threshold = 50
    elif quota_remaining > 5:
        # Very low, only very interesting flights
        threshold = 80
    else:
        # Almost out, only exceptional flights
        threshold = 100

    should_call = score >= threshold

    reason = f"Score: {score} (threshold: {threshold}) - {', '.join(reasons) if reasons else 'Standard commercial'}"

    return should_call, score, reason

def get_priority_stats():
    """Get statistics on what types of flights we're prioritizing"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Count by type in last 30 days
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN origin_airport IS NOT NULL THEN 1 ELSE 0 END) as with_routes
        FROM flights
        WHERE first_seen >= datetime('now', '-30 days')
    ''')

    total, with_routes = cursor.fetchone()

    conn.close()

    return {
        'total_last_30d': total,
        'with_routes': with_routes,
        'route_percentage': (with_routes / total * 100) if total > 0 else 0
    }

if __name__ == "__main__":
    # Test the prioritization
    print("Testing Route Optimizer...\n")

    test_flights = [
        ("RCH345", "AE1234", None),           # Military
        ("N12345", "A12345", "N12345"),       # Private
        ("FDX1234", "A12345", None),          # Cargo
        ("UAL123", "A12345", None),           # Commercial
        ("AAL100", "A12345", None),           # Common commercial
    ]

    for callsign, icao, reg in test_flights:
        should, score, reason = should_call_api(callsign, icao, reg, quota_remaining=50)
        print(f"{callsign:15} → {'CALL API' if should else 'SKIP':10} {reason}")

    print("\n" + "="*80)
    stats = get_priority_stats()
    print(f"Last 30 days: {stats['total_last_30d']} flights, {stats['with_routes']} with routes ({stats['route_percentage']:.1f}%)")
