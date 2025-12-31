#!/usr/bin/env python3
"""Fix aircraft records with inconsistent manufacturer/type code data"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

# Known corrections for aircraft with bad data from OpenSky
CORRECTIONS = {
    # Bell helicopters with Boeing type codes
    'C-GAZF': {  # Bell 429
        'aircraft_type': 'B429',  # Correct type code
        'reason': 'OpenSky has wrong type code B763 (Boeing 767) for Bell 429'
    },
    'C-GAZI': {  # Bell 407
        'aircraft_type': 'B407',  # Correct type code
        'reason': 'OpenSky has ZZZZ (unknown) for Bell 407'
    },
    # Bombardier with Boeing type code
    'C-GFOF': {  # Bombardier Challenger 350
        'aircraft_type': 'CL35',  # Correct type code
        'aircraft_model': 'Challenger 350',  # Cleaner model name
        'reason': 'OpenSky has wrong type code B38M (Boeing 737 MAX) for Bombardier Challenger 350'
    },
    # Airbus A220 (formerly Bombardier CS300) - clean up model name
    'N306DU': {  # Airbus A220-300
        'aircraft_model': 'A220-300',  # Cleaner model name (was BD-500-1A11)
        'reason': 'Standardize A220-300 model name (formerly CSeries)'
    },
}

# Manufacturer to type code prefix mapping (for validation)
MANUFACTURER_TYPE_PREFIXES = {
    'Boeing': ['B7', 'B3'],  # B737, B747, B777, B787, etc.
    'Airbus': ['A3', 'A2', 'A1'],  # A320, A330, A350, A380, etc.
    'Bombardier': ['CRJ', 'DH8', 'CL', 'GL'],  # CRJ, Dash 8, Challenger, Global
    'Embraer': ['E1', 'E2', 'E7', 'E9'],  # E170, E175, E190, E195
    'Bell Helicopter': ['B4', 'B2', 'B5'],  # B407, B429, B206, etc. (Bell models)
    'Beechcraft': ['BE', 'B1', 'B3'],  # BE20, BE30, B350, etc.
    'Cessna': ['C1', 'C2', 'C5', 'C6', 'C7'],  # C172, C208, C525, etc.
}

def main():
    print("=" * 70)
    print("FIX BAD AIRCRAFT DATA")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Apply known corrections
    print("Applying known corrections:")
    for registration, correction in CORRECTIONS.items():
        cursor.execute('''
            SELECT icao, manufacturer, aircraft_type, aircraft_model
            FROM flights
            WHERE registration = ?
            LIMIT 1
        ''', (registration,))

        result = cursor.fetchone()
        if result:
            icao, manufacturer, old_type, old_model = result

            # Build update statement dynamically based on what needs correction
            updates = []
            params = []

            if 'aircraft_type' in correction:
                new_type = correction['aircraft_type']
                updates.append('aircraft_type = ?')
                params.append(new_type)
                print(f"  ✓ {registration} ({manufacturer} {old_model})")
                print(f"    Type code: {old_type} → {new_type}")

            if 'aircraft_model' in correction:
                new_model = correction['aircraft_model']
                updates.append('aircraft_model = ?')
                params.append(new_model)
                if 'aircraft_type' not in correction:
                    print(f"  ✓ {registration} ({manufacturer})")
                print(f"    Model: {old_model} → {new_model}")

            if updates:
                params.append(registration)
                cursor.execute(f'''
                    UPDATE flights
                    SET {', '.join(updates)}
                    WHERE registration = ?
                ''', params)

                print(f"    Reason: {correction['reason']}")
                print()

    # Find and report potential mismatches
    print("Checking for other potential mismatches:")
    cursor.execute('''
        SELECT DISTINCT manufacturer, aircraft_type, aircraft_model, registration
        FROM flights
        WHERE manufacturer IS NOT NULL
        AND aircraft_type IS NOT NULL
        AND manufacturer != ''
        AND aircraft_type != ''
        ORDER BY manufacturer
    ''')

    potential_issues = []
    for manufacturer, aircraft_type, model, registration in cursor.fetchall():
        # Check if type code prefix matches manufacturer
        type_prefix = aircraft_type[:2] if len(aircraft_type) >= 2 else aircraft_type[0]

        if manufacturer in MANUFACTURER_TYPE_PREFIXES:
            valid_prefixes = MANUFACTURER_TYPE_PREFIXES[manufacturer]
            is_valid = any(aircraft_type.startswith(prefix) for prefix in valid_prefixes)

            if not is_valid:
                potential_issues.append({
                    'manufacturer': manufacturer,
                    'type': aircraft_type,
                    'model': model,
                    'registration': registration
                })

    if potential_issues:
        print(f"Found {len(potential_issues)} potential manufacturer/type mismatches:")
        for issue in potential_issues[:10]:  # Show first 10
            print(f"  ⚠️  {issue['manufacturer']} with type code {issue['type']} ({issue['model']}) - {issue['registration']}")
        if len(potential_issues) > 10:
            print(f"  ... and {len(potential_issues) - 10} more")
    else:
        print("  ✓ No additional mismatches found")

    print()
    conn.commit()

    # Show final stats
    cursor.execute('''
        SELECT manufacturer, COUNT(DISTINCT aircraft_type) as type_count, COUNT(*) as flight_count
        FROM flights
        WHERE manufacturer IN ('Bell Helicopter', 'Beechcraft', 'BAE Systems', 'Gulfstream')
        GROUP BY manufacturer
        ORDER BY manufacturer
    ''')

    print("=" * 70)
    print("Updated statistics for specific manufacturers:")
    print("=" * 70)
    for manufacturer, type_count, flight_count in cursor.fetchall():
        print(f"{manufacturer}: {flight_count} flights, {type_count} different types")

    conn.close()

if __name__ == "__main__":
    main()
