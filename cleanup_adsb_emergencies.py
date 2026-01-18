#!/usr/bin/env python3
"""
Clean up false ADS-B emergency records from the database.

This script removes all emergency records that were flagged based on the unreliable
ADS-B emergency field. We now ONLY trust transponder squawk codes 7500/7600/7700.

WHY THIS CLEANUP IS NECESSARY:
==============================
The ADS-B emergency field causes massive false positives:
- Ground testing triggers it
- Low fuel warnings (minfuel) set it
- Medical flights (lifeguard) set it
- Many non-emergency priority statuses set it

Our testing showed regular commercial flights being flagged as emergencies.

THE FIX:
========
Remove all records with emergency_type = 'adsb_emergency'
Keep ONLY records with emergency squawk codes (7500/7600/7700)
"""

import sqlite3
import os
from datetime import datetime

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

# Valid emergency types based on SQUAWK CODES ONLY
VALID_EMERGENCY_TYPES = {'hijacking', 'radio_failure', 'general_emergency'}

def analyze_emergencies():
    """Analyze current emergency records"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print()
    print("=" * 80)
    print("ANALYZING EMERGENCY RECORDS")
    print("=" * 80)
    print()

    # Total emergencies
    cursor.execute("SELECT COUNT(*) FROM flights WHERE emergency = 1")
    total = cursor.fetchone()[0]
    print(f"Total emergency records: {total}")
    print()

    # Count by type
    cursor.execute("""
        SELECT emergency_type, COUNT(*) as count
        FROM flights
        WHERE emergency = 1
        GROUP BY emergency_type
        ORDER BY count DESC
    """)

    types = cursor.fetchall()
    print("Breakdown by emergency type:")
    print("-" * 80)

    false_positives = 0
    true_emergencies = 0

    for emergency_type, count in types:
        if emergency_type in VALID_EMERGENCY_TYPES:
            status = "✓ VALID (squawk code)"
            true_emergencies += count
        else:
            status = "✗ FALSE POSITIVE (ADS-B field)"
            false_positives += count

        print(f"  {emergency_type or 'NULL':20s} : {count:5d} records  {status}")

    print("-" * 80)
    print(f"  {'TRUE EMERGENCIES':20s} : {true_emergencies:5d} records  (7500/7600/7700)")
    print(f"  {'FALSE POSITIVES':20s} : {false_positives:5d} records  (ADS-B field)")
    print()

    # Show sample of false positives
    if false_positives > 0:
        print("Sample of FALSE POSITIVE records (first 10):")
        print("-" * 80)
        cursor.execute("""
            SELECT icao, callsign, squawk, emergency_type, first_seen
            FROM flights
            WHERE emergency = 1
            AND (emergency_type NOT IN ('hijacking', 'radio_failure', 'general_emergency')
                 OR emergency_type IS NULL)
            ORDER BY first_seen DESC
            LIMIT 10
        """)

        for icao, callsign, squawk, etype, first_seen in cursor.fetchall():
            display = callsign or icao
            print(f"  {display:15s} Squawk: {squawk or 'N/A':10s} Type: {etype or 'NULL'}")

        if false_positives > 10:
            print(f"  ... and {false_positives - 10} more")
        print()

    conn.close()
    return false_positives, true_emergencies

def cleanup_false_emergencies(dry_run=True):
    """Remove false emergency records"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("=" * 80)
    if dry_run:
        print("DRY RUN - NO CHANGES WILL BE MADE")
    else:
        print("REMOVING FALSE EMERGENCY RECORDS")
    print("=" * 80)
    print()

    # Count records to be cleaned
    cursor.execute("""
        SELECT COUNT(*)
        FROM flights
        WHERE emergency = 1
        AND (emergency_type NOT IN ('hijacking', 'radio_failure', 'general_emergency')
             OR emergency_type IS NULL)
    """)

    to_clean = cursor.fetchone()[0]

    if to_clean == 0:
        print("✓ No false emergencies found - database is already clean!")
        conn.close()
        return 0

    print(f"Records to clean: {to_clean}")
    print()
    print("These records will be updated:")
    print("  emergency = 1  →  emergency = 0")
    print("  emergency_type = 'adsb_emergency'  →  emergency_type = NULL")
    print()

    if not dry_run:
        # Perform the cleanup
        cursor.execute("""
            UPDATE flights
            SET emergency = 0,
                emergency_type = NULL
            WHERE emergency = 1
            AND (emergency_type NOT IN ('hijacking', 'radio_failure', 'general_emergency')
                 OR emergency_type IS NULL)
        """)

        cleaned = cursor.rowcount
        conn.commit()

        print(f"✓ Cleaned {cleaned} false emergency records")
        print()

        # Verify
        cursor.execute("""
            SELECT COUNT(*)
            FROM flights
            WHERE emergency = 1
            AND (emergency_type NOT IN ('hijacking', 'radio_failure', 'general_emergency')
                 OR emergency_type IS NULL)
        """)

        remaining = cursor.fetchone()[0]

        if remaining == 0:
            print("✓ Verification passed - all false emergencies removed")
        else:
            print(f"⚠️  Warning: {remaining} false emergencies still remain")
    else:
        print("DRY RUN - Run with --fix to apply changes")

    conn.close()
    return to_clean

def show_final_stats():
    """Show final emergency statistics"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print()
    print("=" * 80)
    print("FINAL EMERGENCY STATISTICS")
    print("=" * 80)
    print()

    # Total emergencies after cleanup
    cursor.execute("SELECT COUNT(*) FROM flights WHERE emergency = 1")
    total = cursor.fetchone()[0]

    if total == 0:
        print("✓ No emergency records in database")
        print()
        print("The system will now ONLY flag emergencies for:")
        print("  • Squawk 7500 - Aircraft Hijacking")
        print("  • Squawk 7600 - Radio Failure")
        print("  • Squawk 7700 - General Emergency")
    else:
        print(f"Total TRUE emergencies: {total}")
        print()

        cursor.execute("""
            SELECT emergency_type, COUNT(*) as count,
                   MIN(first_seen) as first_seen,
                   MAX(first_seen) as last_seen
            FROM flights
            WHERE emergency = 1
            GROUP BY emergency_type
            ORDER BY count DESC
        """)

        print("Emergency records by type:")
        print("-" * 80)
        for emergency_type, count, first_seen, last_seen in cursor.fetchall():
            type_name = {
                'hijacking': '7500 - Aircraft Hijacking',
                'radio_failure': '7600 - Radio Failure',
                'general_emergency': '7700 - General Emergency'
            }.get(emergency_type, f'Unknown: {emergency_type}')

            print(f"  {type_name:40s} : {count:5d} records")
        print()

    conn.close()

def main():
    import sys

    dry_run = '--fix' not in sys.argv

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "ADS-B EMERGENCY FALSE POSITIVE CLEANUP" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This script removes false emergency records caused by the unreliable")
    print("ADS-B emergency field. Only squawk codes 7500/7600/7700 are trusted.")
    print()

    # Analyze
    false_count, true_count = analyze_emergencies()

    if false_count == 0:
        print("✓ Database is clean!")
        show_final_stats()
        return

    # Cleanup
    cleaned = cleanup_false_emergencies(dry_run=dry_run)

    # Show final stats (only if we actually fixed)
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
        print("Your tracker now uses ONLY squawk codes for emergency detection:")
        print("  • 7500 = Aircraft Hijacking")
        print("  • 7600 = Radio Failure")
        print("  • 7700 = General Emergency")
        print()
        print("The unreliable ADS-B emergency field is now IGNORED.")
    print()

if __name__ == "__main__":
    main()
