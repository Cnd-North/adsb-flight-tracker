#!/usr/bin/env python3
"""
Add aircraft category column to flights table and categorize existing flights.

Categories:
- Military: Military aircraft, defense forces
- Government: Law enforcement, coast guard, government agencies
- Private: Private/corporate aircraft, business jets
- Commercial: Airlines, cargo carriers
- Special: Medical/MEDEVAC, firefighting, search & rescue
- General Aviation: Small aircraft, flight training
- Unknown: Cannot be categorized
"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def add_category_column():
    """Add category column to flights table"""
    print()
    print("=" * 80)
    print("ADDING AIRCRAFT CATEGORY COLUMN")
    print("=" * 80)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(flights)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'category' in columns:
        print("✓ Category column already exists")
    else:
        print("Adding category column...")
        cursor.execute('''
            ALTER TABLE flights
            ADD COLUMN category TEXT
        ''')
        conn.commit()
        print("✓ Category column added")

    # Create index for fast category queries
    print("Creating category index...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_category
        ON flights(category)
    ''')
    conn.commit()
    print("✓ Category index created")

    conn.close()

def categorize_aircraft(icao, registration, operator, operator_callsign, callsign, aircraft_type):
    """
    Categorize an aircraft based on available information.

    Returns one of: Military, Government, Private, Commercial, Special, General Aviation, Unknown
    """
    icao = (icao or '').upper()
    registration = (registration or '').upper()
    operator = (operator or '').upper()
    operator_callsign = (operator_callsign or '').upper()
    callsign = (callsign or '').upper()
    aircraft_type = (aircraft_type or '').upper()

    # Military indicators
    military_keywords = ['FORCE', 'NAVY', 'ARMY', 'AIR FORCE', 'MARINES', 'MILITARY', 'DEFENSE']
    military_callsigns = ['CNV', 'CFC', 'CANFORCE']  # Canadian Forces

    # US Military ICAO hex ranges (approximate)
    us_military_ranges = [
        (0xADF7C8, 0xAFFFFF),  # US Air Force
        (0xAE0000, 0xAE7FFF),  # US Navy
        (0xAE8000, 0xAEFFFF),  # US Army
        (0xAC0000, 0xAC7FFF),  # USAF additional
    ]

    # Check for military
    if any(keyword in operator for keyword in military_keywords):
        return 'Military'
    if any(keyword in operator_callsign for keyword in military_keywords):
        return 'Military'
    if any(cs in callsign for cs in military_callsigns):
        return 'Military'

    # Check US military hex ranges
    try:
        icao_int = int(icao, 16) if icao else 0
        for start, end in us_military_ranges:
            if start <= icao_int <= end:
                return 'Military'
    except (ValueError, TypeError):
        pass

    # Government indicators
    gov_keywords = ['POLICE', 'SHERIFF', 'COAST GUARD', 'CUSTOMS', 'BORDER', 'GOVERNMENT',
                    'FBI', 'DEA', 'FORESTRY', 'PARKS', 'STATE PATROL']

    if any(keyword in operator for keyword in gov_keywords):
        return 'Government'
    if any(keyword in operator_callsign for keyword in gov_keywords):
        return 'Government'

    # Special operations
    special_keywords = ['AMBULANCE', 'MEDEVAC', 'LIFE FLIGHT', 'AIR AMBULANCE', 'MEDIC',
                       'FIREFIGHTER', 'FIRE', 'RESCUE', 'SEARCH AND RESCUE', 'LIFEGUARD']

    if any(keyword in operator for keyword in special_keywords):
        return 'Special'
    if any(keyword in callsign for keyword in special_keywords):
        return 'Special'

    # Commercial airlines (major indicators)
    commercial_keywords = ['AIRLINES', 'AIRWAYS', 'AIR CANADA', 'WESTJET', 'UNITED', 'DELTA',
                          'AMERICAN', 'SOUTHWEST', 'CARGO', 'EXPRESS', 'FEDEX', 'UPS']

    if any(keyword in operator for keyword in commercial_keywords):
        return 'Commercial'

    # Commercial aircraft types
    commercial_types = ['A320', 'A321', 'A319', 'A330', 'A350', 'B737', 'B738', 'B739',
                       'B77W', 'B787', 'B788', 'B789', 'CRJ', 'E170', 'E175', 'E190',
                       'B752', 'B763', 'B764', 'MD11', 'DC10']

    if any(atype in aircraft_type for atype in commercial_types):
        return 'Commercial'

    # Private/Corporate
    private_keywords = ['CORP', 'CORPORATION', 'LLC', 'INC', 'PRIVATE', 'EXECUTIVE',
                       'AVIATION', 'JET', 'CHARTER']
    private_types = ['C25', 'C50', 'C56', 'C68', 'C750', 'GLF', 'G280', 'G650',
                    'CL60', 'FA7X', 'PC12', 'TBM']

    if any(keyword in operator for keyword in private_keywords):
        return 'Private'
    if any(ptype in aircraft_type for ptype in private_types):
        return 'Private'

    # General Aviation (small aircraft)
    ga_types = ['C172', 'C182', 'C206', 'PA28', 'PA44', 'SR20', 'SR22', 'DA40', 'DA42',
                'BE36', 'BE58', 'P28A', 'C152', 'C150']

    if any(gatype in aircraft_type for gatype in ga_types):
        return 'General Aviation'

    # If we have an operator but couldn't categorize, likely commercial or private
    if operator and len(operator) > 3:
        return 'Commercial'

    return 'Unknown'

def categorize_existing_flights():
    """Categorize all existing flights in the database"""
    print()
    print("=" * 80)
    print("CATEGORIZING EXISTING FLIGHTS")
    print("=" * 80)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get all flights
    cursor.execute('''
        SELECT icao, callsign, registration, operator, operator_callsign, aircraft_type
        FROM flights
        WHERE category IS NULL OR category = ''
    ''')

    flights = cursor.fetchall()
    total = len(flights)

    if total == 0:
        print("✓ All flights already categorized")
        conn.close()
        return

    print(f"Categorizing {total} flights...")
    print()

    categories = {}
    updated = 0

    for icao, callsign, registration, operator, operator_callsign, aircraft_type in flights:
        category = categorize_aircraft(icao, registration, operator, operator_callsign, callsign, aircraft_type)

        cursor.execute('''
            UPDATE flights
            SET category = ?
            WHERE icao = ? AND callsign = ?
        ''', (category, icao, callsign or ''))

        updated += 1
        categories[category] = categories.get(category, 0) + 1

        if updated % 100 == 0:
            print(f"  Processed {updated}/{total} flights...")

    conn.commit()
    conn.close()

    print()
    print(f"✓ Categorized {updated} flights")
    print()
    print("Category breakdown:")
    print("-" * 80)

    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {category:20s} : {count:5d} flights")

    print()

def main():
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AIRCRAFT CATEGORY MIGRATION" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Add column
    add_category_column()

    # Categorize existing flights
    categorize_existing_flights()

    print("=" * 80)
    print("✓ MIGRATION COMPLETE!")
    print("=" * 80)
    print()
    print("Aircraft are now categorized into:")
    print("  • Military - Military aircraft and defense forces")
    print("  • Government - Law enforcement, coast guard, agencies")
    print("  • Private - Private/corporate aircraft, business jets")
    print("  • Commercial - Airlines and cargo carriers")
    print("  • Special - Medical, firefighting, search & rescue")
    print("  • General Aviation - Small aircraft, flight training")
    print("  • Unknown - Cannot be categorized")
    print()

if __name__ == "__main__":
    main()
