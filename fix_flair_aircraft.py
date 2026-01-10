#!/usr/bin/env python3
"""Fix all Flair Airlines aircraft - they only operate Boeing 737 MAX 8"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def main():
    print("=" * 70)
    print("FIX FLAIR AIRLINES AIRCRAFT DATA")
    print("=" * 70)
    print()
    print("Flair Airlines operates an all-Boeing 737 MAX 8 fleet")
    print("Fixing aircraft with FLE callsigns or C-FL registrations...")
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find all Flair Airlines flights (FLE callsign or C-FL registration)
    cursor.execute('''
        SELECT DISTINCT icao, registration, callsign, manufacturer, aircraft_type, aircraft_model
        FROM flights
        WHERE callsign LIKE 'FLE%'
        OR registration LIKE 'C-FL%'
        ORDER BY registration
    ''')

    flair_flights = cursor.fetchall()

    print(f"Found {len(flair_flights)} Flair Airlines aircraft:")
    print()

    fixed = 0
    for icao, registration, callsign, manufacturer, aircraft_type, model in flair_flights:
        # Check if it needs fixing
        needs_fix = (manufacturer != 'Boeing' or
                     aircraft_type != 'B38M' or
                     model != '737 MAX 8')

        if needs_fix:
            print(f"  ✗ {registration or icao} (callsign: {callsign or 'none'})")
            print(f"    Current: {manufacturer or 'no mfr'} | {aircraft_type or 'no type'} | {model or 'no model'}")
            print(f"    Fixing to: Boeing | B38M | 737 MAX 8")

            cursor.execute('''
                UPDATE flights
                SET manufacturer = 'Boeing',
                    aircraft_type = 'B38M',
                    aircraft_model = '737 MAX 8',
                    operator = 'Flair Airlines'
                WHERE icao = ?
            ''', (icao,))

            fixed += 1
            print()
        else:
            print(f"  ✓ {registration or icao} - Already correct")

    conn.commit()

    print()
    print("=" * 70)
    print(f"Fixed {fixed} Flair Airlines aircraft")
    print("=" * 70)

    # Verify
    cursor.execute('''
        SELECT manufacturer, aircraft_type, aircraft_model, COUNT(*) as count
        FROM flights
        WHERE callsign LIKE 'FLE%' OR registration LIKE 'C-FL%'
        GROUP BY manufacturer, aircraft_type, aircraft_model
    ''')

    print()
    print("Flair Airlines fleet after fix:")
    for mfr, atype, model, count in cursor.fetchall():
        print(f"  {mfr} {atype} {model}: {count} flights")

    conn.close()

if __name__ == "__main__":
    main()
