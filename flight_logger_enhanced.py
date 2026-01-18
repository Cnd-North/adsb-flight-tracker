#!/usr/bin/env python3
"""
Enhanced ADS-B Flight Logger with Aircraft & Route Details
Logs all detected flights with complete information from multiple APIs
"""

import json
import requests
import sqlite3
import time
import os
from datetime import datetime

# Import quota management and route optimizer
import api_quota_manager as quota
import route_optimizer

# Configuration
AIRCRAFT_JSON = os.path.expanduser("~/adsb-tracker/dump1090-fa-web/public_html/data/aircraft.json")
DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")
OPENSKY_API = "https://opensky-network.org/api"
UPDATE_INTERVAL = 30  # Check for new aircraft every 30 seconds

# Track seen aircraft to avoid duplicates in same session
seen_flights = set()

# Cache for API results
aircraft_cache = {}
route_cache = {}

# ICAO to IATA airline code mapping (for route lookups)
ICAO_TO_IATA = {
    'ACA': 'AC',   # Air Canada
    'WJA': 'WS',   # WestJet
    'WEN': 'WS',   # WestJet Encore (uses same IATA code)
    'UAL': 'UA',   # United
    'DAL': 'DL',   # Delta
    'AAL': 'AA',   # American
    'ASA': 'AS',   # Alaska
    'JBU': 'B6',   # JetBlue
    'SWA': 'WN',   # Southwest
    'FFT': 'F9',   # Frontier
    'FLE': 'F8',   # Flair Airlines
    'SKW': 'OO',   # SkyWest
    'RPA': 'YX',   # Republic Airways
    'ENY': 'MQ',   # Envoy Air
    'PDT': 'OH',   # Piedmont Airlines
    'CPZ': 'CP',   # Compass Airlines
}

# Aircraft registration prefixes to country mapping
REGISTRATION_COUNTRY_PREFIXES = {
    'C-': 'Canada',
    'N': 'United States',
    'G-': 'United Kingdom',
    'D-': 'Germany',
    'F-': 'France',
    'I-': 'Italy',
    'JA': 'Japan',
    'HL': 'South Korea',
    'B-': 'China',
    'VH-': 'Australia',
    'ZK-': 'New Zealand',
    'XA-': 'Mexico',
    'XB-': 'Mexico',
    'XC-': 'Mexico',
    'CC-': 'Chile',
    'PT-': 'Brazil',
    'PR-': 'Brazil',
    'PP-': 'Brazil',
    'PH-': 'Netherlands',
    'OO-': 'Belgium',
    'LN-': 'Norway',
    'SE-': 'Sweden',
    'OH-': 'Finland',
    'EI-': 'Ireland',
    'HB-': 'Switzerland',
    'TC-': 'Turkey',
    'A6-': 'United Arab Emirates',
    'A7-': 'Qatar',
    'HZ-': 'Saudi Arabia',
    'VT-': 'India',
    '9M-': 'Malaysia',
    'HS-': 'Thailand',
    'RP-': 'Philippines',
    'YV-': 'Venezuela',
    'LV-': 'Argentina',
    'ZS-': 'South Africa',
}

def get_country_from_registration(registration):
    """Determine country from aircraft registration prefix"""
    if not registration:
        return None

    registration = registration.upper().strip()

    # Check each prefix (sorted by length, longest first to match more specific prefixes)
    for prefix, country in sorted(REGISTRATION_COUNTRY_PREFIXES.items(), key=lambda x: -len(x[0])):
        if registration.startswith(prefix):
            return country

    return None

# ICAO aircraft type code to (manufacturer, model) mapping
# This is a fallback when OpenSky doesn't have manufacturer/model data
AIRCRAFT_TYPE_MAP = {
    # Boeing (common types in North America)
    'B737': ('Boeing', '737-700'), 'B738': ('Boeing', '737-800'), 'B739': ('Boeing', '737-900'),
    'B38M': ('Boeing', '737 MAX 8'), 'B39M': ('Boeing', '737 MAX 9'), 'B37M': ('Boeing', '737 MAX 7'),
    'B752': ('Boeing', '757-200'), 'B753': ('Boeing', '757-300'),
    'B762': ('Boeing', '767-200'), 'B763': ('Boeing', '767-300'), 'B764': ('Boeing', '767-400'),
    'B772': ('Boeing', '777-200'), 'B773': ('Boeing', '777-300'), 'B77W': ('Boeing', '777-300ER'),
    'B788': ('Boeing', '787-8'), 'B789': ('Boeing', '787-9'), 'B78X': ('Boeing', '787-10'),
    'B744': ('Boeing', '747-400'), 'B748': ('Boeing', '747-8'),
    # Airbus
    'A319': ('Airbus', 'A319'), 'A320': ('Airbus', 'A320'), 'A321': ('Airbus', 'A321'),
    'A20N': ('Airbus', 'A320neo'), 'A21N': ('Airbus', 'A321neo'),
    'A332': ('Airbus', 'A330-200'), 'A333': ('Airbus', 'A330-300'), 'A339': ('Airbus', 'A330-900neo'),
    'A359': ('Airbus', 'A350-900'), 'A35K': ('Airbus', 'A350-1000'),
    'A380': ('Airbus', 'A380-800'), 'A388': ('Airbus', 'A380-800'),
    # Embraer
    'E170': ('Embraer', 'E170'), 'E175': ('Embraer', 'E175'), 'E75L': ('Embraer', 'E175-E2'),
    'E190': ('Embraer', 'E190'), 'E195': ('Embraer', 'E195'),
    'E135': ('Embraer', 'ERJ-135'), 'E145': ('Embraer', 'ERJ-145'),
    # Bombardier/De Havilland
    'CRJ1': ('Bombardier', 'CRJ100'), 'CRJ2': ('Bombardier', 'CRJ200'),
    'CRJ7': ('Bombardier', 'CRJ700'), 'CRJ9': ('Bombardier', 'CRJ900'), 'CRJX': ('Bombardier', 'CRJ1000'),
    'DH8A': ('Bombardier', 'Dash 8-100'), 'DH8B': ('Bombardier', 'Dash 8-200'),
    'DH8C': ('Bombardier', 'Dash 8-300'), 'DH8D': ('Bombardier', 'Dash 8-400'),
    'GLEX': ('Bombardier', 'Global Express'), 'GL5T': ('Bombardier', 'Global 5000'),
    # Beechcraft/Cessna (common GA/regional)
    'BE20': ('Beechcraft', 'King Air 200'), 'BE30': ('Beechcraft', 'King Air 300'),
    'BE35': ('Beechcraft', 'King Air 350'), 'B350': ('Beechcraft', 'King Air 350'),
    'C208': ('Cessna', '208 Caravan'), 'C172': ('Cessna', '172 Skyhawk'),
    # ATR
    'AT72': ('ATR', 'ATR 72'), 'AT75': ('ATR', 'ATR 72-500'), 'AT76': ('ATR', 'ATR 72-600'),
}

def get_aircraft_from_type_code(aircraft_type):
    """Get manufacturer and model from ICAO aircraft type code"""
    if not aircraft_type:
        return None, None

    aircraft_type = aircraft_type.upper().strip()
    if aircraft_type in AIRCRAFT_TYPE_MAP:
        return AIRCRAFT_TYPE_MAP[aircraft_type]

    return None, None

# Manufacturer name normalization mapping
MANUFACTURER_NORMALIZATION = {
    'Boeing': 'Boeing',
    'The Boeing Company': 'Boeing',
    'Boeing Company': 'Boeing',
    'The Boeing Company Commercial Airplane Division': 'Boeing',
    'Airbus': 'Airbus',
    'Airbus Industrie': 'Airbus',
    'AIRBUS SAS': 'Airbus',
    'Airbus Canada Lp': 'Airbus',
    'Airbus Canada LP': 'Airbus',
    'Bombardier': 'Bombardier',
    'Bombardier Inc': 'Bombardier',
    'Bombardier Inc.': 'Bombardier',
    'Bombardier Aerospace': 'Bombardier',
    'Embraer': 'Embraer',
    'Embraer S A': 'Embraer',
    'Embraer S.A.': 'Embraer',
    'Cessna': 'Cessna',
    'Cessna Aircraft Company': 'Cessna',
    'Cessna Aircraft Co': 'Cessna',
    'Beechcraft': 'Beechcraft',
    'Beech Aircraft Corporation': 'Beechcraft',
    'Raytheon Aircraft Company': 'Beechcraft',
    'Gulfstream': 'Gulfstream',
    'Gulfstream Aerospace': 'Gulfstream',
    'De Havilland Canada': 'De Havilland Canada',
    'Dehavilland': 'De Havilland Canada',
    'ATR': 'ATR',
    'Avions de Transport Regional': 'ATR',
    'McDonnell Douglas': 'McDonnell Douglas',
    'Douglas Aircraft Company': 'McDonnell Douglas',
    'Embraer-empresa Brasileira De': 'Embraer',
    'Embraer-Empresa Brasileira de Aeronautica S.A.': 'Embraer',
    'British Aerospace': 'BAE Systems',
    'British Aerospace P.l.c.': 'BAE Systems',
    'Bell Helicopter': 'Bell Helicopter',
    'Bell Helicopter Textron': 'Bell Helicopter',
    'Bell Helicopter Textron Canada Ltd.': 'Bell Helicopter',
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

def categorize_aircraft(icao, registration, operator, operator_callsign, callsign, aircraft_type):
    """
    Categorize an aircraft based on available information.

    Returns one of: Military, Government, Private, Commercial, Special, General Aviation, Unknown
    """
    icao = (icao or '').upper()
    registration = (registration or '').upper()
    operator = (operator or '').upper()
    operator_callsign = (operator_callsign or '').upper()
    callsign = (callsign or '').upper()
    aircraft_type = (aircraft_type or '').upper()

    # Military indicators
    military_keywords = ['FORCE', 'NAVY', 'ARMY', 'AIR FORCE', 'MARINES', 'MILITARY', 'DEFENSE']
    military_callsigns = ['CNV', 'CFC', 'CANFORCE']  # Canadian Forces

    # US Military ICAO hex ranges (approximate)
    us_military_ranges = [
        (0xADF7C8, 0xAFFFFF),  # US Air Force
        (0xAE0000, 0xAE7FFF),  # US Navy
        (0xAE8000, 0xAEFFFF),  # US Army
        (0xAC0000, 0xAC7FFF),  # USAF additional
    ]

    # Check for military
    if any(keyword in operator for keyword in military_keywords):
        return 'Military'
    if any(keyword in operator_callsign for keyword in military_keywords):
        return 'Military'
    if any(cs in callsign for cs in military_callsigns):
        return 'Military'

    # Check US military hex ranges
    try:
        icao_int = int(icao, 16) if icao else 0
        for start, end in us_military_ranges:
            if start <= icao_int <= end:
                return 'Military'
    except (ValueError, TypeError):
        pass

    # Government indicators
    gov_keywords = ['POLICE', 'SHERIFF', 'COAST GUARD', 'CUSTOMS', 'BORDER', 'GOVERNMENT',
                    'FBI', 'DEA', 'FORESTRY', 'PARKS', 'STATE PATROL']

    if any(keyword in operator for keyword in gov_keywords):
        return 'Government'
    if any(keyword in operator_callsign for keyword in gov_keywords):
        return 'Government'

    # Special operations
    special_keywords = ['AMBULANCE', 'MEDEVAC', 'LIFE FLIGHT', 'AIR AMBULANCE', 'MEDIC',
                       'FIREFIGHTER', 'FIRE', 'RESCUE', 'SEARCH AND RESCUE', 'LIFEGUARD']

    if any(keyword in operator for keyword in special_keywords):
        return 'Special'
    if any(keyword in callsign for keyword in special_keywords):
        return 'Special'

    # Commercial airlines (major indicators)
    commercial_keywords = ['AIRLINES', 'AIRWAYS', 'AIR CANADA', 'WESTJET', 'UNITED', 'DELTA',
                          'AMERICAN', 'SOUTHWEST', 'CARGO', 'EXPRESS', 'FEDEX', 'UPS']

    if any(keyword in operator for keyword in commercial_keywords):
        return 'Commercial'

    # Commercial aircraft types
    commercial_types = ['A320', 'A321', 'A319', 'A330', 'A350', 'B737', 'B738', 'B739',
                       'B77W', 'B787', 'B788', 'B789', 'CRJ', 'E170', 'E175', 'E190',
                       'B752', 'B763', 'B764', 'MD11', 'DC10']

    if any(atype in aircraft_type for atype in commercial_types):
        return 'Commercial'

    # Private/Corporate
    private_keywords = ['CORP', 'CORPORATION', 'LLC', 'INC', 'PRIVATE', 'EXECUTIVE',
                       'AVIATION', 'JET', 'CHARTER']
    private_types = ['C25', 'C50', 'C56', 'C68', 'C750', 'GLF', 'G280', 'G650',
                    'CL60', 'FA7X', 'PC12', 'TBM']

    if any(keyword in operator for keyword in private_keywords):
        return 'Private'
    if any(ptype in aircraft_type for ptype in private_types):
        return 'Private'

    # General Aviation (small aircraft)
    ga_types = ['C172', 'C182', 'C206', 'PA28', 'PA44', 'SR20', 'SR22', 'DA40', 'DA42',
                'BE36', 'BE58', 'P28A', 'C152', 'C150']

    if any(gatype in aircraft_type for gatype in ga_types):
        return 'General Aviation'

    # If we have an operator but couldn't categorize, likely commercial or private
    if operator and len(operator) > 3:
        return 'Commercial'

    return 'Unknown'

# Emergency squawk codes mapping
# These are the ONLY reliable indicators of actual emergencies
EMERGENCY_SQUAWKS = {
    '7500': 'hijacking',       # Aircraft hijacking / unlawful interference
    '7600': 'radio_failure',   # Loss of radio communication
    '7700': 'general_emergency' # General emergency requiring immediate assistance
}

def detect_emergency(aircraft):
    """
    Detect emergency status from aircraft transponder squawk codes.
    Returns (is_emergency, emergency_type)

    IMPORTANT: We ONLY use transponder squawk codes (7500/7600/7700) for emergency detection.

    WHY WE IGNORE THE ADS-B EMERGENCY FIELD:
    ========================================
    The ADS-B emergency field (aircraft.get('emergency')) is UNRELIABLE and causes false positives:

    1. IMPLEMENTATION ISSUES:
       - Many aircraft do not properly implement the ADS-B emergency status message (Type 28)
       - Manufacturers chose not to implement the full emergency register despite it being in the standard
       - The field indicates "there is an emergency but not what type" (Source: IFATCA)

    2. FALSE POSITIVES:
       - Set during ground testing and maintenance
       - Triggered by low fuel warnings (minfuel) - not emergencies
       - Activated for medical flights (lifeguard) - priority but not emergency
       - Radio failure (nordo) - already covered by squawk 7600
       - Many other non-emergency priority statuses

    3. FIELD DEFINITION:
       According to ADS-B Exchange API documentation, the emergency field is a "superset of the
       7×00 squawks" and can indicate: general, lifeguard, minfuel, nordo, unlawful, downed, reserved
       MOST OF THESE ARE NOT ACTUAL EMERGENCIES!

    4. REAL-WORLD EVIDENCE:
       Testing showed regular commercial flights (Air Canada, WestJet) being flagged as emergencies
       with normal squawk codes like 2653, 3247, 4533 - clearly false positives.

    THE GOLD STANDARD - TRANSPONDER SQUAWK CODES:
    ============================================
    - Pilots deliberately set these codes
    - Recognized worldwide by ATC
    - No false positives
    - Clear, specific meaning
    - Industry standard since inception of transponders

    Sources:
    - IFATCA Report: https://ifatca.wiki/kb/wp-2008-89/
    - ADS-B Exchange API: https://www.adsbexchange.com/version-2-api-wip/
    - FAA ATC Manual: https://www.faa.gov/air_traffic/publications/atpubs/atc_html/chap5_section_2.html
    """
    squawk = aircraft.get('squawk')

    # ONLY check squawk codes - ignore ADS-B emergency field
    if squawk in EMERGENCY_SQUAWKS:
        emergency_type = EMERGENCY_SQUAWKS[squawk]
        is_emergency = True
    else:
        emergency_type = None
        is_emergency = False

    return is_emergency, emergency_type

def get_aircraft_details(icao):
    """Get aircraft details from OpenSky Network"""
    if icao in aircraft_cache:
        return aircraft_cache[icao]

    try:
        # OpenSky aircraft database
        url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao.lower()}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # Convert Unix timestamp to year if built date exists
            built_year = None
            if data.get('built'):
                try:
                    built_year = datetime.fromtimestamp(data['built'] / 1000).year
                except:
                    built_year = None

            details = {
                'registration': data.get('registration'),
                'model': data.get('model'),
                'type': data.get('typecode'),
                'manufacturer': normalize_manufacturer(data.get('manufacturerName')),  # Normalize manufacturer name
                'owner': data.get('owner'),
                'built': built_year,
                'operator': data.get('operator'),
                'operator_callsign': data.get('operatorCallsign'),
                'operator_iata': data.get('operatorIata')
            }
            aircraft_cache[icao] = details
            return details
    except Exception as e:
        print(f"  Error fetching aircraft details: {e}")

    return None

def convert_icao_to_iata_callsign(callsign):
    """Convert ICAO callsign to IATA format for API queries"""
    if not callsign or len(callsign) < 3:
        return callsign

    # Extract airline code (first 3 characters) and flight number
    airline_icao = callsign[:3].upper()
    flight_number = callsign[3:].strip()

    # Convert to IATA if we have a mapping
    airline_iata = ICAO_TO_IATA.get(airline_icao)

    if airline_iata:
        return f"{airline_iata}{flight_number}"

    # Return original if no mapping found
    return callsign

def get_flight_route_aviationstack(callsign):
    """Get route from Aviation Stack API (free tier: 100 requests/month)"""
    api_key = os.getenv('AVIATIONSTACK_KEY', '')

    if not api_key:
        return None

    # Check quota before making request
    can_request, status_msg = quota.can_make_request('aviationstack', callsign)
    if not can_request:
        print(f"  ⚠️  Skipping API call: {status_msg}")
        return None

    # Convert ICAO callsign to IATA format (ADS-B uses ICAO, API needs IATA)
    iata_callsign = convert_icao_to_iata_callsign(callsign)

    try:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': api_key,
            'flight_iata': iata_callsign.strip()
        }

        if iata_callsign != callsign:
            print(f"  🔄 Converted {callsign} → {iata_callsign} for API lookup")

        response = requests.get(url, params=params, timeout=5)

        # Record that we made a request (successful or not)
        remaining = quota.record_request('aviationstack')

        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                flight = data['data'][0]
                departure = flight.get('departure', {})
                arrival = flight.get('arrival', {})

                origin = departure.get('iata') or departure.get('icao')
                dest = arrival.get('iata') or arrival.get('icao')

                if origin or dest:
                    print(f"  📊 API quota: {remaining} requests remaining this month")
                    return {
                        'origin': origin,
                        'destination': dest
                    }
    except Exception as e:
        print(f"  Aviation Stack error: {e}")

    return None

def get_flight_route_adsbx(icao, callsign):
    """Try ADS-B Exchange API v2 for live flight data"""
    try:
        # ADSB Exchange v2 endpoint (limited free access)
        url = f"https://api.adsbexchange.com/v2/icao/{icao.lower()}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (flight tracker)'
        }

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if 'ac' in data and len(data['ac']) > 0:
                aircraft = data['ac'][0]
                # ADSB Exchange may have route in 'r' field
                route_str = aircraft.get('r', '')
                if route_str and '-' in route_str:
                    parts = route_str.split('-')
                    if len(parts) == 2:
                        return {
                            'origin': parts[0].strip(),
                            'destination': parts[1].strip()
                        }
    except Exception as e:
        pass

    return None

def get_flight_route(callsign, icao, registration=None):
    """Try to get flight route information from live APIs with smart prioritization"""
    if not callsign or callsign in route_cache:
        return route_cache.get(callsign)

    route = None

    # Try Aviation Stack first (if API key available)
    if os.getenv('AVIATIONSTACK_KEY'):
        # Get current quota remaining
        quota_status = quota.get_quota_status()
        remaining = quota_status['apis']['aviationstack']['remaining']

        # Check if we should call API for this flight
        should_call, score, reason = route_optimizer.should_call_api(
            callsign, icao, registration, remaining
        )

        if should_call:
            print(f"  🎯 Priority API call - {reason}")
            route = get_flight_route_aviationstack(callsign)
            if route:
                print(f"  🛫 Route (AviationStack): {route.get('origin', '?')} → {route.get('destination', '?')}")
        else:
            print(f"  ⏭️  Skipped API call - {reason}")

    # Try ADS-B Exchange as fallback (free, no quota)
    if not route:
        route = get_flight_route_adsbx(icao, callsign)
        if route:
            print(f"  🛫 Route (ADSB-X): {route.get('origin', '?')} → {route.get('destination', '?')}")

    # Cache the result (even if None to avoid repeated lookups)
    route_cache[callsign] = route

    return route

def log_flight(aircraft):
    """Log flight to database with enhanced details"""
    icao = aircraft.get('hex', '').upper()
    callsign = aircraft.get('flight', '').strip()

    if not icao:
        return

    # Use empty string instead of None/blank for callsign to make UNIQUE constraint work
    callsign = callsign if callsign else ''

    # Create unique key for this flight session
    flight_key = f"{icao}_{callsign}_{datetime.now().date()}"

    # Skip if we've already logged this flight today
    if flight_key in seen_flights:
        update_flight(aircraft)
        return

    # Extract additional dump1090 data
    squawk = aircraft.get('squawk')
    is_emergency, emergency_type = detect_emergency(aircraft)
    emergency = 1 if is_emergency else 0
    vertical_rate = aircraft.get('vert_rate')
    latitude = aircraft.get('lat')
    longitude = aircraft.get('lon')
    rssi = aircraft.get('rssi')

    print(f"\n📝 New flight detected: {callsign or icao}")
    if emergency:
        emergency_desc = {
            'hijacking': 'AIRCRAFT HIJACKING',
            'radio_failure': 'RADIO FAILURE',
            'general_emergency': 'GENERAL EMERGENCY',
            'adsb_emergency': 'ADS-B EMERGENCY'
        }.get(emergency_type, 'EMERGENCY')
        print(f"  🚨 {emergency_desc}: Squawk {squawk}")

    # Get aircraft details
    aircraft_details = get_aircraft_details(icao)

    # If OpenSky didn't provide manufacturer/model, try using the aircraft type code
    if aircraft_details:
        if (not aircraft_details.get('manufacturer') or not aircraft_details.get('model')) and aircraft_details.get('type'):
            type_manufacturer, type_model = get_aircraft_from_type_code(aircraft_details['type'])
            if type_manufacturer and type_model:
                if not aircraft_details.get('manufacturer'):
                    aircraft_details['manufacturer'] = type_manufacturer
                if not aircraft_details.get('model'):
                    aircraft_details['model'] = type_model

    # Get route information (only for flights with callsigns)
    registration = aircraft_details.get('registration') if aircraft_details else None
    route_info = get_flight_route(callsign, icao, registration) if callsign else None

    # Determine country (priority: registration prefix > OpenSky metadata > live API)
    country = None

    # Method 1: Use registration prefix (most reliable)
    if aircraft_details and aircraft_details.get('registration'):
        country = get_country_from_registration(aircraft_details['registration'])

    # Method 2: Try OpenSky live states API (only works for currently flying aircraft)
    if not country:
        try:
            url = f"{OPENSKY_API}/states/all?icao24={icao.lower()}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('states') and len(data['states']) > 0:
                    country = data['states'][0][2]
        except:
            pass

    # Default to Unknown if no country found
    if not country:
        country = "Unknown"

    # Categorize aircraft
    category = categorize_aircraft(
        icao,
        aircraft_details.get('registration') if aircraft_details else None,
        aircraft_details.get('operator') if aircraft_details else None,
        aircraft_details.get('operator_callsign') if aircraft_details else None,
        callsign,
        aircraft_details.get('type') if aircraft_details else None
    )

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO flights
            (icao, callsign, origin_country, altitude_max, speed_max, messages_total,
             registration, aircraft_type, aircraft_model, manufacturer, year_built,
             origin_airport, destination_airport, operator, operator_callsign, operator_iata,
             squawk, emergency, emergency_type, vertical_rate, latitude, longitude, signal_rssi, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            icao,
            callsign,  # Already converted to empty string above
            country,
            aircraft.get('altitude'),
            aircraft.get('speed'),
            aircraft.get('messages', 0),
            aircraft_details.get('registration') if aircraft_details else None,
            aircraft_details.get('type') if aircraft_details else None,
            aircraft_details.get('model') if aircraft_details else None,
            aircraft_details.get('manufacturer') if aircraft_details else None,
            aircraft_details.get('built') if aircraft_details else None,
            route_info.get('origin') if route_info else None,
            route_info.get('destination') if route_info else None,
            aircraft_details.get('operator') if aircraft_details else None,
            aircraft_details.get('operator_callsign') if aircraft_details else None,
            aircraft_details.get('operator_iata') if aircraft_details else None,
            squawk,
            emergency,
            emergency_type,
            vertical_rate,
            latitude,
            longitude,
            rssi,
            category
        ))

        conn.commit()

        if cursor.rowcount > 0:
            seen_flights.add(flight_key)
            print(f"  ✓ Logged: {callsign or icao}")
            print(f"  📊 Alt: {aircraft.get('altitude')} ft | Speed: {aircraft.get('speed')} kts")

            if aircraft_details:
                print(f"  ✈️  Registration: {aircraft_details.get('registration')}")
                print(f"  🏭 {aircraft_details.get('manufacturer')} {aircraft_details.get('model')}")
                if aircraft_details.get('built'):
                    print(f"  📅 Built: {aircraft_details.get('built')}")
                if aircraft_details.get('operator'):
                    print(f"  🏢 Operator: {aircraft_details.get('operator')}")

            if route_info:
                origin = route_info.get('origin') or '?'
                dest = route_info.get('destination') or '?'
                print(f"  🛫 Route: {origin} → {dest}")

    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def update_flight(aircraft):
    """Update existing flight with new max values and capture route if missing"""
    icao = aircraft.get('hex', '').upper()
    callsign = aircraft.get('flight', '').strip()

    # Use empty string instead of None/blank for callsign
    callsign = callsign if callsign else ''

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if this flight is missing route data and has a callsign
    if callsign:
        cursor.execute('''
            SELECT origin_airport, destination_airport, registration
            FROM flights
            WHERE icao = ? AND callsign = ? AND DATE(flight_date) = DATE('now')
        ''', (icao, callsign))

        result = cursor.fetchone()
        if result and not result[0] and not result[1]:
            # Flight exists but has no route - try to capture it
            registration = result[2] if len(result) > 2 else None
            route_info = get_flight_route(callsign, icao, registration)
            if route_info:
                cursor.execute('''
                    UPDATE flights
                    SET origin_airport = ?,
                        destination_airport = ?
                    WHERE icao = ? AND callsign = ? AND DATE(flight_date) = DATE('now')
                ''', (
                    route_info.get('origin'),
                    route_info.get('destination'),
                    icao,
                    callsign
                ))
                origin = route_info.get('origin') or '?'
                dest = route_info.get('destination') or '?'
                print(f"  🛫 Route captured: {origin} → {dest}")

    # Extract additional data
    squawk = aircraft.get('squawk')
    is_emergency, emergency_type = detect_emergency(aircraft)
    emergency = 1 if is_emergency else 0
    vertical_rate = aircraft.get('vert_rate')
    latitude = aircraft.get('lat')
    longitude = aircraft.get('lon')
    rssi = aircraft.get('rssi')

    cursor.execute('''
        UPDATE flights
        SET last_seen = CURRENT_TIMESTAMP,
            altitude_max = MAX(altitude_max, ?),
            speed_max = MAX(speed_max, ?),
            messages_total = messages_total + ?,
            squawk = COALESCE(?, squawk),
            emergency = MAX(emergency, ?),
            emergency_type = COALESCE(?, emergency_type),
            vertical_rate = ?,
            latitude = ?,
            longitude = ?,
            signal_rssi = ?,
            time_in_view = CAST((julianday(CURRENT_TIMESTAMP) - julianday(first_seen)) * 86400 AS INTEGER)
        WHERE icao = ? AND callsign = ? AND DATE(flight_date) = DATE('now')
    ''', (
        aircraft.get('altitude') or 0,
        aircraft.get('speed') or 0,
        aircraft.get('messages', 0),
        squawk,
        emergency,
        emergency_type,
        vertical_rate,
        latitude,
        longitude,
        rssi,
        icao,
        callsign  # Already converted to empty string above
    ))

    conn.commit()
    conn.close()

def read_dump1090_data():
    """Read aircraft data from dump1090"""
    try:
        with open(AIRCRAFT_JSON, 'r') as f:
            data = json.load(f)
            return data.get('aircraft', [])
    except Exception as e:
        return []

def get_stats():
    """Get logging statistics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM flights')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM flights WHERE flight_date = DATE('now')")
    today = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT origin_country) FROM flights')
    countries = cursor.fetchone()[0]

    conn.close()

    return total, today, countries

def main():
    """Main logging loop"""
    print("=" * 80)
    print("ENHANCED ADS-B FLIGHT LOGGER")
    print("=" * 80)
    print()
    print(f"✓ Database: {DATABASE}")
    print(f"✓ Update interval: {UPDATE_INTERVAL} seconds")
    print(f"✓ Features: Aircraft details + Live route lookup")
    print()

    # Check for API keys
    has_aviationstack = bool(os.getenv('AVIATIONSTACK_KEY'))

    print("📡 Route Data Sources:")
    if has_aviationstack:
        # Show quota status
        quota_status = quota.get_quota_status()
        aviationstack_quota = quota_status['apis']['aviationstack']
        remaining = aviationstack_quota['remaining']
        used = aviationstack_quota['used']
        total = aviationstack_quota['total']

        print(f"  ✓ Aviation Stack API: {remaining}/{total} requests remaining ({used} used)")

        # Show priority airline list
        if remaining <= 20:
            print(f"  ⚠️  Low quota - prioritizing: {', '.join(quota.PRIORITY_AIRLINES)}")
    else:
        print("  ○ Aviation Stack - No API key (sign up: https://aviationstack.com/)")
    print("  ✓ ADS-B Exchange API (limited free access)")
    print()

    if not has_aviationstack:
        print("💡 Tip: Get free Aviation Stack API key for better route coverage:")
        print("   1. Sign up: https://aviationstack.com/product")
        print("   2. Get your API key from dashboard")
        print("   3. Run: export AVIATIONSTACK_KEY='your-key-here'")
        print("   4. Restart this logger")
        print()

    total, today, countries = get_stats()
    print(f"📊 Current stats:")
    print(f"   Total flights logged: {total}")
    print(f"   Flights today: {today}")
    print(f"   Countries seen: {countries}")
    print()
    print("Starting enhanced flight logger... (Press Ctrl+C to stop)")
    print("=" * 80)

    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Read current aircraft
            aircraft_list = read_dump1090_data()

            # Log each aircraft with good signal
            new_count = 0
            for aircraft in aircraft_list:
                # Only log aircraft with reasonable signal (>20 messages)
                if aircraft.get('messages', 0) > 20:
                    messages_before = len(seen_flights)
                    log_flight(aircraft)
                    if len(seen_flights) > messages_before:
                        new_count += 1

            if new_count > 0:
                total, today, countries = get_stats()
                print(f"\n📊 [{timestamp}] Stats: {today} today | {total} total | {countries} countries")
            else:
                print(f"[{timestamp}] Monitoring... ({len(aircraft_list)} aircraft visible)")

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n")
        print("=" * 80)
        print("Shutting down enhanced flight logger")
        print("=" * 80)
        total, today, countries = get_stats()
        print(f"\nFinal statistics:")
        print(f"  Flights logged today: {today}")
        print(f"  Total flights in database: {total}")
        print(f"  Countries observed: {countries}")
        print(f"  Aircraft details cached: {len(aircraft_cache)}")

        # Show final quota status
        if os.getenv('AVIATIONSTACK_KEY'):
            print(f"\nAPI Quota Status:")
            quota_status = quota.get_quota_status()
            aviationstack_quota = quota_status['apis']['aviationstack']
            print(f"  Aviation Stack: {aviationstack_quota['used']}/{aviationstack_quota['total']} used")
            print(f"  Remaining this month: {aviationstack_quota['remaining']}")

        print(f"\nDatabase saved to: {DATABASE}")
        print(f"View your log at: http://localhost:8080/log.html")
        print()

if __name__ == "__main__":
    main()
