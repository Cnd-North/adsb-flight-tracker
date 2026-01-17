#!/usr/bin/env python3
"""
Fix false emergency records in the database.
Only squawk codes 7500, 7600, 7700 should be marked as emergencies.
"""

import sqlite3
import os
from collections import defaultdict

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

# Valid emergency squawk codes
EMERGENCY_SQUAWKS = {'7500', '7600', '7700'}

def analyze_emergencies():
    """Analyze current emergency records and identify false positives"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("=" * 80)
    print("ANALYZING EMERGENCY RECORDS")
    print("=" * 80)
    print()

    # Get all records marked as emergency
    cursor.execute('''
        SELECT icao, callsign, squawk, emergency_type, first_seen
        FROM flights
        WHERE emergency = 1
        ORDER BY first_seen DESC
    ''')

    emergency_records = cursor.fetchall()
    total_emergencies = len(emergency_records)

    print(f"Total records marked as emergency: {total_emergencies}")
    print()

    # Categorize by squawk code
    squawk_counts = defaultdict(int)
    false_positives = []
    true_emergencies = []

    for record in emergency_records:
        icao, callsign, squawk, emergency_type, first_seen = record
        squawk_counts[squawk or 'NULL'] += 1

        # Check if this is a valid emergency
        if squawk in EMERGENCY_SQUAWKS:
            true_emergencies.append(record)
        else:
            false_positives.append(record)

    print("Emergency records by squawk code:")
    print("-" * 80)
    for squawk in sorted(squawk_counts.keys(), key=lambda x: squawk_counts[x], reverse=True):
        count = squawk_counts[squawk]
        is_valid = "✓ VALID" if squawk in EMERGENCY_SQUAWKS else "✗ FALSE"
        print(f"  {squawk:10s} : {count:5d} records  {is_valid}")

    print()
    print("=" * 80)
    print(f"✓ True emergencies (7500/7600/7700): {len(true_emergencies)}")
    print(f"✗ False positives (other squawks):   {len(false_positives)}")
    print("=" * 80)
    print()

    conn.close()

    return len(false_positives), squawk_counts

def fix_false_emergencies(dry_run=True):
    """Fix false emergency records"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print()
    print("=" * 80)
    if dry_run:
        print("DRY RUN - NO CHANGES WILL BE MADE")
    else:
        print("FIXING FALSE EMERGENCY RECORDS")
    print("=" * 80)
    print()

    # Find all false emergencies (emergency = 1 but squawk is not 7500/7600/7700)
    cursor.execute('''
        SELECT icao, callsign, squawk, emergency_type, first_seen
        FROM flights
        WHERE emergency = 1
        AND (squawk IS NULL OR squawk NOT IN ('7500', '7600', '7700'))
    ''')

    false_emergencies = cursor.fetchall()

    if not false_emergencies:
        print("✓ No false emergencies found - database is clean!")
        conn.close()
        return 0

    print(f"Found {len(false_emergencies)} false emergency records to fix")
    print()

    # Show sample of records that will be fixed
    print("Sample of records to be fixed (first 10):")
    print("-" * 80)
    for i, record in enumerate(false_emergencies[:10]):
        icao, callsign, squawk, emergency_type, first_seen = record
        print(f"  {i+1}. {callsign or icao:15s} Squawk: {squawk or 'NULL':10s} Type: {emergency_type or 'NULL'}")

    if len(false_emergencies) > 10:
        print(f"  ... and {len(false_emergencies) - 10} more")

    print()

    if not dry_run:
        # Fix the records
        cursor.execute('''
            UPDATE flights
            SET emergency = 0,
                emergency_type = NULL
            WHERE emergency = 1
            AND (squawk IS NULL OR squawk NOT IN ('7500', '7600', '7700'))
        ''')

        fixed_count = cursor.rowcount
        conn.commit()

        print(f"✓ Fixed {fixed_count} false emergency records")
        print()

        # Verify the fix
        cursor.execute('''
            SELECT COUNT(*)
            FROM flights
            WHERE emergency = 1
            AND (squawk IS NULL OR squawk NOT IN ('7500', '7600', '7700'))
        ''')

        remaining = cursor.fetchone()[0]

        if remaining == 0:
            print("✓ Verification passed - no false emergencies remain")
        else:
            print(f"⚠️  Warning: {remaining} false emergencies still remain")
    else:
        print("DRY RUN - Run with --fix flag to apply changes")
        fixed_count = len(false_emergencies)

    conn.close()
    return fixed_count

def show_final_stats():
    """Show final emergency statistics"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print()
    print("=" * 80)
    print("FINAL EMERGENCY STATISTICS")
    print("=" * 80)
    print()

    # Count by emergency type
    cursor.execute('''
        SELECT
            emergency_type,
            COUNT(*) as count,
            MIN(first_seen) as first_seen,
            MAX(first_seen) as last_seen
        FROM flights
        WHERE emergency = 1
        GROUP BY emergency_type
        ORDER BY count DESC
    ''')

    results = cursor.fetchall()

    print("Emergency records by type:")
    print("-" * 80)
    total = 0
    for emergency_type, count, first_seen, last_seen in results:
        total += count
        type_name = {
            'hijacking': '7500 - Aircraft Hijacking',
            'radio_failure': '7600 - Radio Failure',
            'general_emergency': '7700 - General Emergency',
            'adsb_emergency': 'ADS-B Emergency (no squawk)'
        }.get(emergency_type, f'Unknown: {emergency_type}')

        print(f"  {type_name:40s} : {count:5d} records")

    print("-" * 80)
    print(f"  {'TOTAL':40s} : {total:5d} records")
    print()

    conn.close()

def main():
    import sys

    # Check if --fix flag is provided
    dry_run = '--fix' not in sys.argv

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "EMERGENCY RECORDS CLEANUP TOOL" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Step 1: Analyze
    false_count, squawk_counts = analyze_emergencies()

    if false_count == 0:
        print("✓ Database is clean - no false emergencies found!")
        show_final_stats()
        return

    # Step 2: Fix
    fixed_count = fix_false_emergencies(dry_run=dry_run)

    # Step 3: Show final stats (only if we actually fixed)
    if not dry_run:
        show_final_stats()

    print()
    if dry_run:
        print("=" * 80)
        print("To apply these changes, run:")
        print(f"  python3 {sys.argv[0]} --fix")
        print("=" * 80)
    else:
        print("=" * 80)
        print("✓ CLEANUP COMPLETE!")
        print("=" * 80)
        print()
        print("View updated statistics at: http://localhost:8080/stats.html")
    print()

if __name__ == "__main__":
    main()
