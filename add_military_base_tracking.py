#!/usr/bin/env python3
"""
Add military base tracking to flights table and identify existing military operations.

Tracks flights taking off from or landing at military bases, even if the aircraft
itself is not categorized as military.
"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

# Comprehensive list of military base ICAO codes
# Format: ICAO code -> (Name, Country)
MILITARY_BASES = {
    # Canadian Forces Bases (CFB)
    'CYTR': ('CFB Trenton', 'Canada'),
    'CYQQ': ('CFB Comox', 'Canada'),
    'CYOD': ('CFB Cold Lake', 'Canada'),
    'CYWG': ('CFB Winnipeg', 'Canada'),
    'CYAW': ('CFB Shearwater', 'Canada'),
    'CYQF': ('CFB Bagotville', 'Canada'),
    'CYXY': ('CFB Whitehorse', 'Canada'),
    'CYQY': ('CFB Goose Bay', 'Canada'),
    'CYYR': ('CFB Goose Bay', 'Canada'),
    'CYHZ': ('CFB Halifax/Shearwater', 'Canada'),
    'CYQB': ('CFB Valcartier (Quebec)', 'Canada'),
    'CYYC': ('CFB Calgary (SARCUP)', 'Canada'),

    # US Air Force Bases
    'KSUU': ('Travis AFB', 'United States'),
    'KEDW': ('Edwards AFB', 'United States'),
    'KLSV': ('Nellis AFB', 'United States'),
    'KDOV': ('Dover AFB', 'United States'),
    'KOFF': ('Offutt AFB', 'United States'),
    'KMCF': ('MacDill AFB', 'United States'),
    'KDMA': ('Davis-Monthan AFB', 'United States'),
    'KLUF': ('Luke AFB', 'United States'),
    'KBAD': ('Barksdale AFB', 'United States'),
    'KEND': ('Vance AFB', 'United States'),
    'KTIK': ('Tinker AFB', 'United States'),
    'KRCA': ('Ellsworth AFB', 'United States'),
    'KFFO': ('Wright-Patterson AFB', 'United States'),
    'KRIV': ('March ARB', 'United States'),
    'KMHZ': ('Moody AFB', 'United States'),
    'KBLV': ('Scott AFB', 'United States'),
    'KDYS': ('Dyess AFB', 'United States'),
    'KBAB': ('Beale AFB', 'United States'),
    'Khmn': ('Holloman AFB', 'United States'),
    'KHIF': ('Hill AFB', 'United States'),
    'KSPS': ('Sheppard AFB', 'United States'),
    'KVPS': ('Eglin AFB', 'United States'),
    'KNKX': ('MCAS Miramar', 'United States'),
    'KPIA': ('Greater Peoria Airport (ANG Base)', 'United States'),
    'KNGP': ('NAS Corpus Christi', 'United States'),
    'KNEW': ('Lakefront Airport (NAS JRB)', 'United States'),
    'KMUO': ('Mountain Home AFB', 'United States'),
    'KSAV': ('Hunter AAF/Savannah', 'United States'),
    'KLFI': ('Langley AFB', 'United States'),
    'KGRF': ('Gray AAF', 'United States'),
    'KNTU': ('NAS Oceana', 'United States'),

    # US Naval Air Stations (NAS)
    'KNHK': ('NAS Patuxent River', 'United States'),
    'KNSE': ('NAS Whiting Field', 'United States'),
    'KNIP': ('NAS Jacksonville', 'United States'),
    'KNQI': ('NAS Kingsville', 'United States'),
    'KNPA': ('NAS Pensacola', 'United States'),
    'KNBC': ('NAS Beaufort', 'United States'),
    'KNOW': ('NAS Key West', 'United States'),
    'KNZY': ('NAS North Island', 'United States'),
    'KNFL': ('NAS Fallon', 'United States'),
    'KNUW': ('NAS Whidbey Island', 'United States'),
    'KNGU': ('NAS Norfolk', 'United States'),
    'KNKT': ('NAS Cherry Point', 'United States'),
    'KNJK': ('NAS El Centro', 'United States'),
    'KNLC': ('NAS Lemoore', 'United States'),

    # US Army Airfields
    'KHOP': ('Fort Campbell AAF', 'United States'),
    'KFRI': ('Fort Riley Marshall AAF', 'United States'),
    'KFCS': ('Fort Carson Butts AAF', 'United States'),
    'KFSI': ('Fort Sill Henry Post AAF', 'United States'),
    'KFBG': ('Fort Bragg Simmons AAF', 'United States'),
    'KFDK': ('Fort Detrick', 'United States'),
    'KFHU': ('Fort Huachuca Libby AAF', 'United States'),
    'KILG': ('Fort Dix', 'United States'),
    'KFME': ('Fort Meade Tipton AAF', 'United States'),

    # US Marine Corps Air Stations (MCAS)
    'KNKX': ('MCAS Miramar', 'United States'),
    'KNYL': ('MCAS Yuma', 'United States'),
    'KBAB': ('MCAS Twentynine Palms', 'United States'),
    'KNHK': ('MCAS New River', 'United States'),
    'KNCA': ('MCAS Camp Pendleton', 'United States'),

    # Other notable military airfields
    'KPOB': ('Pope AAF', 'United States'),
    'KDLF': ('Laughlin AFB', 'United States'),
    'KCBM': ('Columbus AFB', 'United States'),
    'KVAD': ('Moody AFB', 'United States'),
    'KRND': ('Randolph AFB', 'United States'),
    'KSKF': ('Lackland AFB', 'United States'),
    'KBIX': ('Keesler AFB', 'United States'),
    'KMXF': ('Maxwell AFB', 'United States'),
    'KGUS': ('Grissom ARB', 'United States'),
    'KADW': ('Andrews AFB/Joint Base Andrews', 'United States'),
    'KBWI': ('Martin State Airport (ANG)', 'United States'),
    'KCHK': ('Chickasha Municipal (USAF)', 'United States'),

    # Coast Guard Air Stations
    'KAIA': ('CGAS Clearwater', 'United States'),
    'KAST': ('CGAS Astoria', 'United States'),
    'KBLI': ('CGAS Bellingham', 'United States'),
    'TJSJ': ('CGAS Borinquen', 'Puerto Rico'),
    'KDET': ('CGAS Detroit', 'United States'),
    'KEYW': ('CGAS Key West', 'United States'),
}

def add_military_base_columns():
    """Add military base tracking columns to flights table"""
    print()
    print("=" * 80)
    print("ADDING MILITARY BASE TRACKING COLUMNS")
    print("=" * 80)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(flights)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'military_base_activity' not in columns:
        print("Adding military_base_activity column...")
        cursor.execute('''
            ALTER TABLE flights
            ADD COLUMN military_base_activity INTEGER DEFAULT 0
        ''')
        conn.commit()
        print("✓ military_base_activity column added")
    else:
        print("✓ military_base_activity column already exists")

    if 'military_base_name' not in columns:
        print("Adding military_base_name column...")
        cursor.execute('''
            ALTER TABLE flights
            ADD COLUMN military_base_name TEXT
        ''')
        conn.commit()
        print("✓ military_base_name column added")
    else:
        print("✓ military_base_name column already exists")

    # Create index for fast military base queries
    print("Creating military base index...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_military_base
        ON flights(military_base_activity)
    ''')
    conn.commit()
    print("✓ Military base index created")

    conn.close()

def identify_military_base_operations():
    """Identify and flag existing flights operating at military bases"""
    print()
    print("=" * 80)
    print("IDENTIFYING MILITARY BASE OPERATIONS")
    print("=" * 80)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get all flights
    cursor.execute('''
        SELECT icao, callsign, origin_airport, destination_airport
        FROM flights
        WHERE (origin_airport IS NOT NULL OR destination_airport IS NOT NULL)
        AND (military_base_activity IS NULL OR military_base_activity = 0)
    ''')

    flights = cursor.fetchall()
    total = len(flights)

    if total == 0:
        print("✓ All flights already analyzed")
        conn.close()
        return

    print(f"Analyzing {total} flights for military base operations...")
    print()

    military_ops = 0
    base_counts = {}

    for icao, callsign, origin, destination in flights:
        military_base = None
        base_name = None

        # Check origin
        if origin in MILITARY_BASES:
            military_base = 1
            base_info = MILITARY_BASES[origin]
            base_name = f"{base_info[0]} ({origin})"
            base_counts[base_name] = base_counts.get(base_name, 0) + 1

        # Check destination
        if destination in MILITARY_BASES:
            military_base = 1
            base_info = MILITARY_BASES[destination]
            dest_base_name = f"{base_info[0]} ({destination})"

            if base_name:
                # Both origin and destination are military bases
                base_name = f"{base_name} → {dest_base_name}"
            else:
                base_name = dest_base_name

            base_counts[dest_base_name] = base_counts.get(dest_base_name, 0) + 1

        if military_base:
            cursor.execute('''
                UPDATE flights
                SET military_base_activity = ?,
                    military_base_name = ?
                WHERE icao = ? AND callsign = ?
            ''', (military_base, base_name, icao, callsign or ''))

            military_ops += 1

            if military_ops % 10 == 0:
                print(f"  Found {military_ops} military base operations...")

    conn.commit()
    conn.close()

    print()
    print(f"✓ Identified {military_ops} military base operations")
    print()

    if base_counts:
        print("Most active military bases:")
        print("-" * 80)
        for base, count in sorted(base_counts.items(), key=lambda x: -x[1])[:15]:
            print(f"  {base:50s} : {count:4d} operations")

    print()

def main():
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "MILITARY BASE TRACKING MIGRATION" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Add columns
    add_military_base_columns()

    # Identify military base operations
    identify_military_base_operations()

    print("=" * 80)
    print("✓ MIGRATION COMPLETE!")
    print("=" * 80)
    print()
    print(f"Now tracking {len(MILITARY_BASES)} military bases across North America:")
    print("  • Canadian Forces Bases (CFB)")
    print("  • US Air Force Bases (AFB)")
    print("  • US Naval Air Stations (NAS)")
    print("  • US Army Airfields (AAF)")
    print("  • US Marine Corps Air Stations (MCAS)")
    print("  • US Coast Guard Air Stations (CGAS)")
    print()
    print("Flights operating at these bases are now flagged, even if the")
    print("aircraft itself is not categorized as military!")
    print()

if __name__ == "__main__":
    main()
