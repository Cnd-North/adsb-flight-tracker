#!/usr/bin/env python3
"""Remove duplicate flight entries, keeping the most complete record"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")

def main():
    print("=" * 70)
    print("DUPLICATE FLIGHT REMOVAL")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find duplicates (same ICAO + registration on same date)
    cursor.execute('''
        SELECT icao, registration, flight_date, COUNT(*) as count
        FROM flights
        WHERE registration IS NOT NULL
        GROUP BY icao, registration, flight_date
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
    for icao, registration, flight_date, count in duplicates[:10]:
        print(f"  {icao} ({registration}) on {flight_date}: {count} entries")
    print()

    total_removed = 0

    # For each set of duplicates, keep the best record and delete the rest
    for icao, registration, flight_date, count in duplicates:
        # Get all duplicate records
        cursor.execute('''
            SELECT id, icao, callsign, registration, manufacturer, aircraft_model,
                   altitude_max, speed_max, messages_total, origin_airport, destination_airport,
                   first_seen, last_seen
            FROM flights
            WHERE icao = ? AND registration = ? AND flight_date = ?
            ORDER BY messages_total DESC, altitude_max DESC, first_seen ASC
        ''', (icao, registration, flight_date))

        records = cursor.fetchall()

        if len(records) <= 1:
            continue

        # Keep the first record (best one based on sorting)
        keep_id = records[0][0]

        # Collect best data from all records
        best_callsign = None
        best_manufacturer = None
        best_model = None
        best_altitude = 0
        best_speed = 0
        total_messages = 0
        best_origin = None
        best_dest = None
        earliest_seen = records[0][11]
        latest_seen = records[0][12]

        for record in records:
            _, _, callsign, _, manufacturer, model, alt, speed, msgs, origin, dest, first, last = record

            if callsign and not best_callsign:
                best_callsign = callsign
            if manufacturer and not best_manufacturer:
                best_manufacturer = manufacturer
            if model and not best_model:
                best_model = model
            if alt and alt > best_altitude:
                best_altitude = alt
            if speed and speed > best_speed:
                best_speed = speed
            if msgs:
                total_messages += msgs
            if origin and not best_origin:
                best_origin = origin
            if dest and not best_dest:
                best_dest = dest
            if first < earliest_seen:
                earliest_seen = first
            if last > latest_seen:
                latest_seen = last

        # Update the kept record with best data from all duplicates
        cursor.execute('''
            UPDATE flights
            SET callsign = COALESCE(?, callsign),
                manufacturer = COALESCE(?, manufacturer),
                aircraft_model = COALESCE(?, aircraft_model),
                altitude_max = ?,
                speed_max = ?,
                messages_total = ?,
                origin_airport = COALESCE(?, origin_airport),
                destination_airport = COALESCE(?, destination_airport),
                first_seen = ?,
                last_seen = ?
            WHERE id = ?
        ''', (best_callsign, best_manufacturer, best_model, best_altitude, best_speed,
              total_messages, best_origin, best_dest, earliest_seen, latest_seen, keep_id))

        # Delete the duplicate records
        delete_ids = [r[0] for r in records[1:]]
        cursor.execute(f'''
            DELETE FROM flights
            WHERE id IN ({','.join('?' * len(delete_ids))})
        ''', delete_ids)

        removed = len(delete_ids)
        total_removed += removed
        print(f"✓ {icao} ({registration}): Merged {len(records)} records into 1, removed {removed}")

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
