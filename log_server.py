#!/usr/bin/env python3
"""
Simple API server for flight log database
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
from urllib.parse import parse_qs, urlparse

DATABASE = os.path.expanduser("~/radioconda/Projects/flight_log.db")
PORT = 8081

class LogAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/flights':
            self.serve_flights()
        elif path == '/api/stats':
            self.serve_stats()
        elif path == '/api/analytics':
            self.serve_analytics()
        else:
            self.send_error(404)

    def serve_flights(self):
        """Serve flight log data as JSON"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    icao,
                    callsign,
                    first_seen,
                    last_seen,
                    origin_country,
                    origin_airport,
                    destination_airport,
                    altitude_max,
                    speed_max,
                    messages_total,
                    flight_date,
                    registration,
                    aircraft_type,
                    aircraft_model,
                    manufacturer,
                    year_built,
                    operator,
                    operator_callsign,
                    operator_iata,
                    squawk,
                    emergency,
                    vertical_rate,
                    latitude,
                    longitude,
                    time_in_view,
                    signal_rssi
                FROM flights
                ORDER BY first_seen DESC
                LIMIT 1000
            ''')

            flights = [dict(row) for row in cursor.fetchall()]
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(flights, indent=2).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_stats(self):
        """Serve statistics as JSON"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # Total flights
            cursor.execute('SELECT COUNT(*) FROM flights')
            total = cursor.fetchone()[0]

            # Today's flights
            cursor.execute("SELECT COUNT(*) FROM flights WHERE flight_date = DATE('now')")
            today = cursor.fetchone()[0]

            # Unique countries
            cursor.execute('SELECT COUNT(DISTINCT origin_country) FROM flights')
            countries = cursor.fetchone()[0]

            # Max altitude
            cursor.execute('SELECT MAX(altitude_max) FROM flights')
            max_alt = cursor.fetchone()[0] or 0

            # Max speed
            cursor.execute('SELECT MAX(speed_max) FROM flights')
            max_speed = cursor.fetchone()[0] or 0

            conn.close()

            stats = {
                'total_flights': total,
                'today_flights': today,
                'countries_count': countries,
                'max_altitude': max_alt,
                'max_speed': max_speed
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats, indent=2).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_analytics(self):
        """Serve detailed analytics as JSON"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Unique aircraft
            cursor.execute('SELECT COUNT(DISTINCT icao) FROM flights')
            unique_aircraft = cursor.fetchone()[0]

            # Top manufacturers
            cursor.execute('''
                SELECT manufacturer, COUNT(*) as count
                FROM flights
                WHERE manufacturer IS NOT NULL
                GROUP BY manufacturer
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_manufacturers = [dict(row) for row in cursor.fetchall()]

            # Top models
            cursor.execute('''
                SELECT aircraft_model, manufacturer, COUNT(*) as count
                FROM flights
                WHERE aircraft_model IS NOT NULL
                GROUP BY aircraft_model, manufacturer
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_models = [dict(row) for row in cursor.fetchall()]

            # Top operators
            cursor.execute('''
                SELECT operator, operator_callsign, COUNT(*) as count
                FROM flights
                WHERE operator IS NOT NULL AND operator != ''
                GROUP BY operator, operator_callsign
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_operators = [dict(row) for row in cursor.fetchall()]

            # Emergency events
            cursor.execute('''
                SELECT icao, callsign, squawk, first_seen, manufacturer, aircraft_model
                FROM flights
                WHERE emergency = 1
                ORDER BY first_seen DESC
            ''')
            emergencies = [dict(row) for row in cursor.fetchall()]

            # Countries seen
            cursor.execute('''
                SELECT origin_country, COUNT(*) as count
                FROM flights
                WHERE origin_country IS NOT NULL
                GROUP BY origin_country
                ORDER BY count DESC
            ''')
            countries = [dict(row) for row in cursor.fetchall()]

            # Flights by hour
            cursor.execute('''
                SELECT CAST(strftime('%H', first_seen) AS INTEGER) as hour, COUNT(*) as count
                FROM flights
                GROUP BY hour
                ORDER BY hour
            ''')
            by_hour = [dict(row) for row in cursor.fetchall()]

            # Altitude records
            cursor.execute('''
                SELECT icao, callsign, altitude_max, manufacturer, aircraft_model, registration
                FROM flights
                WHERE altitude_max IS NOT NULL
                ORDER BY altitude_max DESC
                LIMIT 10
            ''')
            altitude_records = [dict(row) for row in cursor.fetchall()]

            # Speed records
            cursor.execute('''
                SELECT icao, callsign, speed_max, manufacturer, aircraft_model, registration
                FROM flights
                WHERE speed_max IS NOT NULL
                ORDER BY speed_max DESC
                LIMIT 10
            ''')
            speed_records = [dict(row) for row in cursor.fetchall()]

            # Rarest aircraft (seen only once)
            cursor.execute('''
                SELECT manufacturer, aircraft_model, COUNT(*) as count
                FROM flights
                WHERE manufacturer IS NOT NULL
                GROUP BY manufacturer, aircraft_model
                HAVING count = 1
                ORDER BY manufacturer, aircraft_model
            ''')
            rare_aircraft = [dict(row) for row in cursor.fetchall()]

            # Top origin airports
            cursor.execute('''
                SELECT origin_airport, COUNT(*) as count
                FROM flights
                WHERE origin_airport IS NOT NULL AND origin_airport != ''
                GROUP BY origin_airport
                ORDER BY count DESC
                LIMIT 15
            ''')
            top_origins = [dict(row) for row in cursor.fetchall()]

            # Top destination airports
            cursor.execute('''
                SELECT destination_airport, COUNT(*) as count
                FROM flights
                WHERE destination_airport IS NOT NULL AND destination_airport != ''
                GROUP BY destination_airport
                ORDER BY count DESC
                LIMIT 15
            ''')
            top_destinations = [dict(row) for row in cursor.fetchall()]

            # Most common routes
            cursor.execute('''
                SELECT origin_airport, destination_airport, COUNT(*) as count
                FROM flights
                WHERE origin_airport IS NOT NULL AND origin_airport != ''
                AND destination_airport IS NOT NULL AND destination_airport != ''
                GROUP BY origin_airport, destination_airport
                ORDER BY count DESC
                LIMIT 15
            ''')
            top_routes = [dict(row) for row in cursor.fetchall()]

            conn.close()

            analytics = {
                'unique_aircraft': unique_aircraft,
                'top_manufacturers': top_manufacturers,
                'top_models': top_models,
                'top_operators': top_operators,
                'emergencies': emergencies,
                'countries': countries,
                'flights_by_hour': by_hour,
                'altitude_records': altitude_records,
                'speed_records': speed_records,
                'rare_aircraft': rare_aircraft,
                'top_origins': top_origins,
                'top_destinations': top_destinations,
                'top_routes': top_routes
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(analytics, indent=2).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def main():
    server = HTTPServer(('localhost', PORT), LogAPIHandler)
    print("=" * 80)
    print(f"Flight Log API Server")
    print("=" * 80)
    print(f"Database: {DATABASE}")
    print(f"Listening on: http://localhost:{PORT}")
    print()
    print(f"API Endpoints:")
    print(f"  GET http://localhost:{PORT}/api/flights  - Get all flights")
    print(f"  GET http://localhost:{PORT}/api/stats    - Get statistics")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down API server...")
        server.shutdown()

if __name__ == "__main__":
    main()
