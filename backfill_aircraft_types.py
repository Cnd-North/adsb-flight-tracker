#!/usr/bin/env python3
"""Backfill aircraft manufacturer/model data from ICAO aircraft type codes"""

import sqlite3
import os

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")

# ICAO aircraft type code to (manufacturer, model) mapping
# Source: ICAO Document 8643 - Aircraft Type Designators
AIRCRAFT_TYPE_MAP = {
    # Boeing
    'B703': ('Boeing', '707-320'),
    'B712': ('Boeing', '717-200'),
    'B721': ('Boeing', '727-100'),
    'B722': ('Boeing', '727-200'),
    'B731': ('Boeing', '737-100'),
    'B732': ('Boeing', '737-200'),
    'B733': ('Boeing', '737-300'),
    'B734': ('Boeing', '737-400'),
    'B735': ('Boeing', '737-500'),
    'B736': ('Boeing', '737-600'),
    'B737': ('Boeing', '737-700'),
    'B738': ('Boeing', '737-800'),
    'B739': ('Boeing', '737-900'),
    'B37M': ('Boeing', '737 MAX 7'),
    'B38M': ('Boeing', '737 MAX 8'),
    'B39M': ('Boeing', '737 MAX 9'),
    'B3XM': ('Boeing', '737 MAX 10'),
    'B741': ('Boeing', '747-100'),
    'B742': ('Boeing', '747-200'),
    'B743': ('Boeing', '747-300'),
    'B744': ('Boeing', '747-400'),
    'B748': ('Boeing', '747-8'),
    'B752': ('Boeing', '757-200'),
    'B753': ('Boeing', '757-300'),
    'B762': ('Boeing', '767-200'),
    'B763': ('Boeing', '767-300'),
    'B764': ('Boeing', '767-400'),
    'B772': ('Boeing', '777-200'),
    'B773': ('Boeing', '777-300'),
    'B77L': ('Boeing', '777-200LR'),
    'B77W': ('Boeing', '777-300ER'),
    'B778': ('Boeing', '777-8'),
    'B779': ('Boeing', '777-9'),
    'B788': ('Boeing', '787-8'),
    'B789': ('Boeing', '787-9'),
    'B78X': ('Boeing', '787-10'),

    # Airbus
    'A306': ('Airbus', 'A300-600'),
    'A30B': ('Airbus', 'A300B4'),
    'A310': ('Airbus', 'A310'),
    'A318': ('Airbus', 'A318'),
    'A319': ('Airbus', 'A319'),
    'A320': ('Airbus', 'A320'),
    'A321': ('Airbus', 'A321'),
    'A19N': ('Airbus', 'A319neo'),
    'A20N': ('Airbus', 'A320neo'),
    'A21N': ('Airbus', 'A321neo'),
    'A332': ('Airbus', 'A330-200'),
    'A333': ('Airbus', 'A330-300'),
    'A338': ('Airbus', 'A330-800neo'),
    'A339': ('Airbus', 'A330-900neo'),
    'A342': ('Airbus', 'A340-200'),
    'A343': ('Airbus', 'A340-300'),
    'A345': ('Airbus', 'A340-500'),
    'A346': ('Airbus', 'A340-600'),
    'A359': ('Airbus', 'A350-900'),
    'A35K': ('Airbus', 'A350-1000'),
    'A380': ('Airbus', 'A380-800'),
    'A388': ('Airbus', 'A380-800'),

    # Embraer
    'E135': ('Embraer', 'ERJ-135'),
    'E145': ('Embraer', 'ERJ-145'),
    'E170': ('Embraer', 'E170'),
    'E175': ('Embraer', 'E175'),
    'E75L': ('Embraer', 'E175-E2'),
    'E75S': ('Embraer', 'E175 (short)'),
    'E190': ('Embraer', 'E190'),
    'E195': ('Embraer', 'E195'),
    'E290': ('Embraer', 'E190-E2'),
    'E295': ('Embraer', 'E195-E2'),

    # Bombardier
    'CRJ1': ('Bombardier', 'CRJ100'),
    'CRJ2': ('Bombardier', 'CRJ200'),
    'CRJ7': ('Bombardier', 'CRJ700'),
    'CRJ9': ('Bombardier', 'CRJ900'),
    'CRJX': ('Bombardier', 'CRJ1000'),
    'DH8A': ('Bombardier', 'Dash 8-100'),
    'DH8B': ('Bombardier', 'Dash 8-200'),
    'DH8C': ('Bombardier', 'Dash 8-300'),
    'DH8D': ('Bombardier', 'Dash 8-400'),
    'DHC6': ('De Havilland Canada', 'DHC-6 Twin Otter'),
    'DHC7': ('De Havilland Canada', 'DHC-7 Dash 7'),
    'DHC8': ('Bombardier', 'Dash 8'),
    'CL30': ('Bombardier', 'Challenger 300'),
    'CL35': ('Bombardier', 'Challenger 350'),
    'CL60': ('Bombardier', 'Challenger 600'),
    'GLEX': ('Bombardier', 'Global Express'),
    'GL5T': ('Bombardier', 'Global 5000'),
    'GL7T': ('Bombardier', 'Global 7500'),

    # ATR
    'AT42': ('ATR', 'ATR 42'),
    'AT43': ('ATR', 'ATR 42-300'),
    'AT44': ('ATR', 'ATR 42-400'),
    'AT45': ('ATR', 'ATR 42-500'),
    'AT72': ('ATR', 'ATR 72'),
    'AT73': ('ATR', 'ATR 72-200'),
    'AT75': ('ATR', 'ATR 72-500'),
    'AT76': ('ATR', 'ATR 72-600'),

    # McDonnell Douglas
    'DC86': ('McDonnell Douglas', 'DC-8-60'),
    'DC87': ('McDonnell Douglas', 'DC-8-70'),
    'DC91': ('McDonnell Douglas', 'DC-9-10'),
    'DC92': ('McDonnell Douglas', 'DC-9-20'),
    'DC93': ('McDonnell Douglas', 'DC-9-30'),
    'DC94': ('McDonnell Douglas', 'DC-9-40'),
    'DC95': ('McDonnell Douglas', 'DC-9-50'),
    'MD11': ('McDonnell Douglas', 'MD-11'),
    'MD81': ('McDonnell Douglas', 'MD-81'),
    'MD82': ('McDonnell Douglas', 'MD-82'),
    'MD83': ('McDonnell Douglas', 'MD-83'),
    'MD87': ('McDonnell Douglas', 'MD-87'),
    'MD88': ('McDonnell Douglas', 'MD-88'),
    'MD90': ('McDonnell Douglas', 'MD-90'),

    # Cessna
    'C150': ('Cessna', '150'),
    'C152': ('Cessna', '152'),
    'C172': ('Cessna', '172 Skyhawk'),
    'C182': ('Cessna', '182 Skylane'),
    'C206': ('Cessna', '206 Stationair'),
    'C208': ('Cessna', '208 Caravan'),
    'C25A': ('Cessna', 'Citation CJ2'),
    'C25B': ('Cessna', 'Citation CJ3'),
    'C25C': ('Cessna', 'Citation CJ4'),
    'C510': ('Cessna', 'Citation Mustang'),
    'C525': ('Cessna', 'Citation CJ'),
    'C550': ('Cessna', 'Citation II'),
    'C560': ('Cessna', 'Citation V'),
    'C650': ('Cessna', 'Citation III'),
    'C680': ('Cessna', 'Citation Sovereign'),
    'C750': ('Cessna', 'Citation X'),

    # Beechcraft
    'BE20': ('Beechcraft', 'King Air 200'),
    'BE30': ('Beechcraft', 'King Air 300'),
    'BE35': ('Beechcraft', 'King Air 350'),
    'BE40': ('Beechcraft', 'Beechjet 400'),
    'BE58': ('Beechcraft', 'Baron 58'),
    'BE9L': ('Beechcraft', 'King Air 90'),
    'BE9T': ('Beechcraft', 'King Air 100'),
    'B190': ('Beechcraft', 'King Air 100'),
    'B350': ('Beechcraft', 'King Air 350'),

    # Gulfstream
    'G150': ('Gulfstream', 'G150'),
    'G280': ('Gulfstream', 'G280'),
    'G450': ('Gulfstream', 'G450'),
    'G550': ('Gulfstream', 'G550'),
    'G650': ('Gulfstream', 'G650'),
    'GLF4': ('Gulfstream', 'G400'),
    'GLF5': ('Gulfstream', 'G500'),
    'GLF6': ('Gulfstream', 'G600'),
    'GLEX': ('Gulfstream', 'G-IV'),

    # Other common types
    'A124': ('Antonov', 'An-124'),
    'A225': ('Antonov', 'An-225'),
    'A306': ('Airbus', 'A300-600'),
    'IL76': ('Ilyushin', 'Il-76'),
    'IL96': ('Ilyushin', 'Il-96'),
    'T154': ('Tupolev', 'Tu-154'),
    'T204': ('Tupolev', 'Tu-204'),
}

def main():
    print("=" * 70)
    print("AIRCRAFT TYPE CODE BACKFILL")
    print("=" * 70)
    print()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find flights with aircraft type code but missing manufacturer/model
    cursor.execute('''
        SELECT icao, aircraft_type, registration
        FROM flights
        WHERE aircraft_type IS NOT NULL
        AND (manufacturer IS NULL OR manufacturer = ''
             OR aircraft_model IS NULL OR aircraft_model = '')
    ''')

    flights_to_update = cursor.fetchall()

    print(f"Found {len(flights_to_update)} flights with type codes but missing details")
    print()

    # Group by aircraft type to show what we'll update
    cursor.execute('''
        SELECT aircraft_type, COUNT(*) as count
        FROM flights
        WHERE aircraft_type IS NOT NULL
        AND (manufacturer IS NULL OR manufacturer = ''
             OR aircraft_model IS NULL OR aircraft_model = '')
        GROUP BY aircraft_type
        ORDER BY count DESC
    ''')

    print("Aircraft types to update:")
    for aircraft_type, count in cursor.fetchall():
        if aircraft_type in AIRCRAFT_TYPE_MAP:
            manufacturer, model = AIRCRAFT_TYPE_MAP[aircraft_type]
            print(f"  {aircraft_type}: {count} flights → {manufacturer} {model}")
        else:
            print(f"  {aircraft_type}: {count} flights → ⚠️  Unknown type code")
    print()

    updated = 0
    unknown_types = set()

    for icao, aircraft_type, registration in flights_to_update:
        if aircraft_type in AIRCRAFT_TYPE_MAP:
            manufacturer, model = AIRCRAFT_TYPE_MAP[aircraft_type]

            cursor.execute('''
                UPDATE flights
                SET manufacturer = ?,
                    aircraft_model = ?
                WHERE icao = ?
            ''', (manufacturer, model, icao))

            updated += 1
            print(f"✓ {icao} ({registration}): {aircraft_type} → {manufacturer} {model}")
        else:
            unknown_types.add(aircraft_type)

    conn.commit()

    print()
    print("=" * 70)
    print(f"Updated {updated} flights with aircraft details")
    if unknown_types:
        print(f"Unknown type codes: {', '.join(sorted(unknown_types))}")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    main()
