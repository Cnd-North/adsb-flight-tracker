#!/usr/bin/env python3
"""Fix aircraft with completely wrong manufacturer/model data from OpenSky"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

# Known corrections based on external verification (FlightRadar24, ADS-B Exchange, etc.)
AIRCRAFT_CORRECTIONS = {
    'C-FIBA': {
        'manufacturer': 'Boeing',
        'aircraft_type': 'B38M',
        'aircraft_model': '737 MAX 8',
        'operator': 'WestJet',
        'reason': 'OpenSky incorrectly lists as BAE Systems Jetstream - actually Boeing 737 MAX 8',
        'source': 'Verified on FlightRadar24, PlaneLogger, AirNav'
    },
    'C-GAZI': {
        'manufacturer': 'Boeing',
        'aircraft_type': 'B763',
        'aircraft_model': '767-300ER',
        'operator': 'Cargojet Airways',
        'reason': 'OpenSky incorrectly lists as Bell 407 helicopter - actually Boeing 767-300ER freighter',
        'source': 'Verified on RadarBox, AirNav, Airfleets'
    },
    'C-GAZF': {
        'manufacturer': 'Boeing',
        'aircraft_type': 'B763',
        'aircraft_model': '767-300ER',
        'operator': 'Cargojet Airways',
        'reason': 'OpenSky incorrectly lists as Bell 429 helicopter - actually Boeing 767-300ER freighter',
        'source': 'Verified on RadarBox, AirNav, Airfleets'
    },
    'C-FHYY': {
        'manufacturer': 'Airbus',
        'aircraft_type': 'A223',
        'aircraft_model': 'A220-300',
        'operator': 'Air Canada',
        'reason': 'OpenSky incorrectly lists as Cessna C172 trainer - actually Airbus A220-300 (brand new Dec 2025 delivery)',
        'source': 'Verified on JetPhotos, Air Canada fleet records'
    },
}

def main():
    print("=" * 70)
    print("FIX CORRUPTED AIRCRAFT DATA")
    print("=" * 70)
    print()
    print("OpenSky database has severely corrupted data for several aircraft.")
    print("Applying verified corrections from external sources...")
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    fixed = 0
    for registration, correction in AIRCRAFT_CORRECTIONS.items():
        # Check if this aircraft exists in our database
        cursor.execute('''
            SELECT icao, manufacturer, aircraft_type, aircraft_model, operator
            FROM flights
            WHERE registration = ?
            LIMIT 1
        ''', (registration,))

        result = cursor.fetchone()
        if result:
            icao, old_mfr, old_type, old_model, old_operator = result

            print(f"✗ {registration} (ICAO: {icao})")
            print(f"  Current (WRONG): {old_mfr or 'no mfr'} {old_type or 'no type'} {old_model or 'no model'}")
            print(f"  Fixing to: {correction['manufacturer']} {correction['aircraft_type']} {correction['aircraft_model']}")
            print(f"  Operator: {correction['operator']}")
            print(f"  Reason: {correction['reason']}")
            print(f"  Source: {correction['source']}")

            # Update all flights for this aircraft
            cursor.execute('''
                UPDATE flights
                SET manufacturer = ?,
                    aircraft_type = ?,
                    aircraft_model = ?,
                    operator = ?
                WHERE icao = ?
            ''', (
                correction['manufacturer'],
                correction['aircraft_type'],
                correction['aircraft_model'],
                correction['operator'],
                icao
            ))

            fixed += 1
            print()
        else:
            print(f"⚠️  {registration} not found in database")
            print()

    conn.commit()

    print("=" * 70)
    print(f"Fixed {fixed} aircraft with corrupted data")
    print("=" * 70)

    # Show updated manufacturer distribution
    cursor.execute('''
        SELECT manufacturer, COUNT(*) as count
        FROM flights
        WHERE manufacturer IS NOT NULL
        GROUP BY manufacturer
        ORDER BY count DESC
    ''')

    print()
    print("Updated manufacturer distribution:")
    for manufacturer, count in cursor.fetchall():
        print(f"  {manufacturer}: {count}")

    # Show what happened to the false manufacturers
    print()
    print("Verification - checking for remaining false manufacturers:")
    cursor.execute('''
        SELECT manufacturer, COUNT(*) as count
        FROM flights
        WHERE manufacturer IN ('Bell Helicopter', 'BAE Systems')
        GROUP BY manufacturer
    ''')

    remaining = cursor.fetchall()
    if remaining:
        for manufacturer, count in remaining:
            print(f"  {manufacturer}: {count} flights remaining")
    else:
        print("  ✓ All false Bell Helicopter and BAE Systems entries removed")

    # Check Cessna entries
    cursor.execute('''
        SELECT registration, callsign, aircraft_model
        FROM flights
        WHERE manufacturer = 'Cessna'
    ''')
    cessna_entries = cursor.fetchall()
    if cessna_entries:
        print()
        print("Remaining Cessna entries:")
        for reg, call, model in cessna_entries:
            print(f"  {reg} ({call or 'no callsign'}): {model}")

    conn.close()

if __name__ == "__main__":
    main()
