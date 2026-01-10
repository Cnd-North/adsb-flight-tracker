#!/usr/bin/env python3
"""Remove duplicate flight entries by keeping only the most recent/complete one"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def main():
    print("=" * 70)
    print("DUPLICATE FLIGHT REMOVAL")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find duplicates (same ICAO + date, treating NULL callsign as empty string)
    cursor.execute('''
        SELECT icao, COALESCE(callsign, ''), flight_date, COUNT(*) as count
        FROM flights
        GROUP BY icao, COALESCE(callsign, ''), flight_date
        HAVING count > 1
        ORDER BY count DESC
    ''')

    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} sets of duplicate flights")
    print()

    if len(duplicates) == 0:
        print("✓ No duplicates found!")
        conn.close()
        return

    # Show top duplicates
    print("Top 10 duplicates:")
    for icao, callsign, flight_date, count in duplicates[:10]:
        cs_display = callsign if callsign else '(no callsign)'
        print(f"  {icao} {cs_display} on {flight_date}: {count} entries")
    print()

    total_removed = 0

    # For each set of duplicates, keep the best record and delete the rest
    for icao, callsign_coalesced, flight_date, count in duplicates:
        # Convert back empty string to NULL for query
        callsign = callsign_coalesced if callsign_coalesced else None

        # Get all duplicate records for this ICAO/callsign/date combination
        if callsign:
            cursor.execute('''
                SELECT id, messages_total, altitude_max, first_seen
                FROM flights
                WHERE icao = ? AND callsign = ? AND flight_date = ?
                ORDER BY messages_total DESC, altitude_max DESC, first_seen ASC
            ''', (icao, callsign, flight_date))
        else:
            cursor.execute('''
                SELECT id, messages_total, altitude_max, first_seen
                FROM flights
                WHERE icao = ? AND callsign IS NULL AND flight_date = ?
                ORDER BY messages_total DESC, altitude_max DESC, first_seen ASC
            ''', (icao, flight_date))

        records = cursor.fetchall()

        if len(records) <= 1:
            continue

        # Keep the first record (best one based on sorting)
        keep_id = records[0][0]

        # Delete all others
        delete_ids = [r[0] for r in records[1:]]
        cursor.execute(f'''
            DELETE FROM flights
            WHERE id IN ({','.join('?' * len(delete_ids))})
        ''', delete_ids)

        removed = len(delete_ids)
        total_removed += removed

        cs_display = callsign if callsign else '(no callsign)'
        print(f"✓ {icao} {cs_display}: Kept best of {len(records)} records, removed {removed}")

    conn.commit()

    print()
    print("=" * 70)
    print(f"Total duplicate records removed: {total_removed}")
    print("=" * 70)

    # Show final stats
    cursor.execute("SELECT COUNT(*) FROM flights")
    total = cursor.fetchone()[0]
    print(f"Flights remaining in database: {total}")

    conn.close()

if __name__ == "__main__":
    main()
