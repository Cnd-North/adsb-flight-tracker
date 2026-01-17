#!/usr/bin/env python3
"""
Database migration: Add emergency_type column to flights table
"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

def add_emergency_type_column():
    """Add emergency_type column to flights table"""

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("=" * 70)
    print("DATABASE MIGRATION: Adding emergency_type column")
    print("=" * 70)
    print()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(flights)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'emergency_type' in column_names:
        print("✓ Column 'emergency_type' already exists")
        conn.close()
        return

    # Add the new column
    try:
        cursor.execute('''
            ALTER TABLE flights
            ADD COLUMN emergency_type TEXT
        ''')

        conn.commit()
        print("✓ Added 'emergency_type' column to flights table")

        # Update existing emergency records to identify their type based on squawk code
        cursor.execute('''
            UPDATE flights
            SET emergency_type = CASE
                WHEN squawk = '7500' THEN 'hijacking'
                WHEN squawk = '7600' THEN 'radio_failure'
                WHEN squawk = '7700' THEN 'general_emergency'
                ELSE NULL
            END
            WHERE emergency = 1
        ''')

        updated = cursor.rowcount
        conn.commit()

        if updated > 0:
            print(f"✓ Updated {updated} existing emergency record(s) with emergency type")

    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        conn.close()
        return

    # Show updated schema
    cursor.execute("PRAGMA table_info(flights)")
    columns = cursor.fetchall()

    print()
    print("📊 Updated Flights Table Schema:")
    print()
    for col in columns:
        marker = "NEW →" if col[1] == 'emergency_type' else "      "
        print(f"  {marker} {col[1]:25s} {col[2]:10s}")

    conn.close()

    print()
    print("=" * 70)
    print("✓ Migration completed successfully!")
    print("=" * 70)
    print()

if __name__ == "__main__":
    add_emergency_type_column()
