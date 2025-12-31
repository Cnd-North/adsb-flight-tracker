#!/usr/bin/env python3
"""Normalize manufacturer names to standardized versions"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

# Manufacturer normalization mapping
# Maps various name variations to a single canonical name
MANUFACTURER_NORMALIZATION = {
    # Boeing variants
    'Boeing': 'Boeing',
    'The Boeing Company': 'Boeing',
    'Boeing Company': 'Boeing',
    'The Boeing Company Commercial Airplane Division': 'Boeing',
    'BOEING': 'Boeing',

    # Airbus variants
    'Airbus': 'Airbus',
    'AIRBUS': 'Airbus',
    'Airbus Industrie': 'Airbus',
    'AIRBUS SAS': 'Airbus',
    'Airbus Canada Lp': 'Airbus',
    'Airbus Canada LP': 'Airbus',

    # Bombardier variants
    'Bombardier': 'Bombardier',
    'Bombardier Inc': 'Bombardier',
    'Bombardier Inc.': 'Bombardier',
    'Bombardier Aerospace': 'Bombardier',

    # Embraer variants
    'Embraer': 'Embraer',
    'Embraer S A': 'Embraer',
    'Embraer S.A.': 'Embraer',
    'EMBRAER': 'Embraer',

    # Cessna variants
    'Cessna': 'Cessna',
    'Cessna Aircraft Company': 'Cessna',
    'Cessna Aircraft Co': 'Cessna',
    'CESSNA': 'Cessna',

    # Beechcraft variants
    'Beechcraft': 'Beechcraft',
    'Beech Aircraft Corporation': 'Beechcraft',
    'Raytheon Aircraft Company': 'Beechcraft',

    # Gulfstream variants
    'Gulfstream': 'Gulfstream',
    'Gulfstream Aerospace': 'Gulfstream',

    # De Havilland variants
    'De Havilland Canada': 'De Havilland Canada',
    'Dehavilland': 'De Havilland Canada',
    'DHC': 'De Havilland Canada',

    # ATR variants
    'ATR': 'ATR',
    'Avions de Transport Regional': 'ATR',

    # McDonnell Douglas variants
    'McDonnell Douglas': 'McDonnell Douglas',
    'Douglas Aircraft Company': 'McDonnell Douglas',

    # Embraer additional variants
    'Embraer-empresa Brasileira De': 'Embraer',
    'Embraer-Empresa Brasileira de Aeronautica S.A.': 'Embraer',

    # British Aerospace/BAE
    'British Aerospace': 'BAE Systems',
    'British Aerospace P.l.c.': 'BAE Systems',
    'BAE Systems': 'BAE Systems',

    # Bell Helicopter
    'Bell Helicopter': 'Bell Helicopter',
    'Bell Helicopter Textron': 'Bell Helicopter',
    'Bell Helicopter Textron Canada Ltd.': 'Bell Helicopter',
    'Bell Aircraft Corporation': 'Bell Helicopter',
}

def normalize_manufacturer(manufacturer):
    """Normalize manufacturer name to canonical form"""
    if not manufacturer:
        return manufacturer

    # Try exact match first
    if manufacturer in MANUFACTURER_NORMALIZATION:
        return MANUFACTURER_NORMALIZATION[manufacturer]

    # Try case-insensitive match
    for variant, canonical in MANUFACTURER_NORMALIZATION.items():
        if manufacturer.lower() == variant.lower():
            return canonical

    # Return as-is if no mapping found
    return manufacturer

def main():
    print("=" * 70)
    print("MANUFACTURER NAME NORMALIZATION")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Show current distribution
    cursor.execute('''
        SELECT manufacturer, COUNT(*) as count
        FROM flights
        WHERE manufacturer IS NOT NULL
        GROUP BY manufacturer
        ORDER BY count DESC
    ''')

    print("Current manufacturer distribution:")
    current_distribution = cursor.fetchall()
    for manufacturer, count in current_distribution:
        print(f"  {manufacturer}: {count}")
    print()

    # Get all unique manufacturers
    cursor.execute('''
        SELECT DISTINCT manufacturer
        FROM flights
        WHERE manufacturer IS NOT NULL
    ''')

    manufacturers = [row[0] for row in cursor.fetchall()]

    # Create normalization plan
    normalization_plan = {}
    for manufacturer in manufacturers:
        normalized = normalize_manufacturer(manufacturer)
        if normalized != manufacturer:
            normalization_plan[manufacturer] = normalized

    if not normalization_plan:
        print("✓ All manufacturer names are already normalized!")
        conn.close()
        return

    print("Normalization plan:")
    for old_name, new_name in normalization_plan.items():
        cursor.execute('SELECT COUNT(*) FROM flights WHERE manufacturer = ?', (old_name,))
        count = cursor.fetchone()[0]
        print(f"  {old_name} ({count}) → {new_name}")
    print()

    # Apply normalization
    updated = 0
    for old_name, new_name in normalization_plan.items():
        cursor.execute('''
            UPDATE flights
            SET manufacturer = ?
            WHERE manufacturer = ?
        ''', (new_name, old_name))
        updated += cursor.rowcount

    conn.commit()

    print(f"✓ Updated {updated} flight records")
    print()

    # Show new distribution
    cursor.execute('''
        SELECT manufacturer, COUNT(*) as count
        FROM flights
        WHERE manufacturer IS NOT NULL
        GROUP BY manufacturer
        ORDER BY count DESC
    ''')

    print("=" * 70)
    print("Normalized manufacturer distribution:")
    print("=" * 70)
    for manufacturer, count in cursor.fetchall():
        print(f"  {manufacturer}: {count}")

    conn.close()

if __name__ == "__main__":
    main()
