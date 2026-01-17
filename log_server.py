#!/usr/bin/env python3
"""
Simple API server for flight log database
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
import subprocess
from urllib.parse import parse_qs, urlparse

DATABASE = os.path.expanduser("~/adsb-tracker/flight_log.db")
PORT = 8081

def is_process_running(pattern):
    """Check if a process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', pattern],
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

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
        elif path == '/api/status':
            self.serve_status()
        elif path == '/api/coverage':
            self.serve_coverage()
        elif path == '/api/heatmap':
            self.serve_heatmap()
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
                    emergency_type,
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
                SELECT icao, callsign, squawk, emergency_type, first_seen, manufacturer, aircraft_model
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

    def serve_status(self):
        """Serve system status information"""
        try:
            # Check which services are running
            # Note: log_server is always True since we're running this code
            services = {
                'dump1090': is_process_running('dump1090.*--net'),
                'flight_logger': is_process_running('flight_logger_enhanced.py'),
                'log_server': True,  # If we're serving this, we're running
                'position_tracker': is_process_running('position_tracker.py'),
                'signal_logger': is_process_running('signal_logger.py'),
                'web_server': is_process_running('python.*http.server.*8080')
            }

            # Get database stats
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM flights")
            total_flights = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM flights WHERE DATE(first_seen) = DATE('now')")
            flights_today = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM signal_quality")
            positions_logged = cursor.fetchone()[0]

            conn.close()

            status = {
                'services': services,
                'database': {
                    'total_flights': total_flights,
                    'flights_today': flights_today,
                    'positions_logged': positions_logged
                }
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_coverage(self):
        """Serve coverage analysis data"""
        try:
            import math
            from collections import defaultdict

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # Get antenna location (weighted by signal strength)
            cursor.execute('''
                SELECT latitude, longitude, altitude, distance, rssi
                FROM signal_quality
                WHERE latitude IS NOT NULL AND rssi IS NOT NULL
                ORDER BY rssi DESC
                LIMIT 50
            ''')

            positions = cursor.fetchall()

            if not positions:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No position data available'}).encode())
                return

            # Calculate antenna location (weighted by RSSI)
            weighted_lat = sum(p[0] / (abs(p[4]) + 1) for p in positions)
            weighted_lon = sum(p[1] / (abs(p[4]) + 1) for p in positions)
            total_weight = sum(1.0 / (abs(p[4]) + 1) for p in positions)

            antenna_lat = weighted_lat / total_weight
            antenna_lon = weighted_lon / total_weight

            # Estimate antenna height
            closest = [p for p in positions if p[2] and p[3]][:10]
            heights = []
            for lat, lon, alt, dist, rssi in closest:
                alt_m = alt * 0.3048
                dist_m = dist * 1000
                if dist_m > 0:
                    heights.append(max(0, alt_m - dist_m * 0.1))

            antenna_height_m = sum(heights) / len(heights) if heights else 0
            antenna_height_ft = antenna_height_m * 3.28084

            # Get all positions for coverage analysis
            cursor.execute('''
                SELECT latitude, longitude, altitude, rssi
                FROM signal_quality
                WHERE latitude IS NOT NULL
            ''')

            all_positions = cursor.fetchall()

            # Calculate coverage by direction
            def get_bearing(lat1, lon1, lat2, lon2):
                dlon = math.radians(lon2 - lon1)
                y = math.sin(dlon) * math.cos(math.radians(lat2))
                x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
                     math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon))
                bearing = math.degrees(math.atan2(y, x))
                return (bearing + 360) % 360

            def get_distance(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat/2)**2 +
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                     math.sin(dlon/2)**2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            # Coverage by direction (16 directions)
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                         'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

            direction_data = {d: {'count': 0, 'max_distance': 0, 'avg_rssi': []}
                            for d in directions}

            for lat, lon, alt, rssi in all_positions:
                bearing = get_bearing(antenna_lat, antenna_lon, lat, lon)
                distance = get_distance(antenna_lat, antenna_lon, lat, lon)

                # Convert bearing to direction
                dir_index = int((bearing + 11.25) / 22.5) % 16
                direction = directions[dir_index]

                direction_data[direction]['count'] += 1
                direction_data[direction]['max_distance'] = max(
                    direction_data[direction]['max_distance'],
                    distance
                )
                if rssi:
                    direction_data[direction]['avg_rssi'].append(rssi)

            # Format for polar chart
            coverage_by_direction = []
            for direction in directions:
                data = direction_data[direction]
                avg_rssi = (sum(data['avg_rssi']) / len(data['avg_rssi'])
                           if data['avg_rssi'] else None)
                coverage_by_direction.append({
                    'direction': direction,
                    'count': data['count'],
                    'max_distance': round(data['max_distance'], 1),
                    'avg_rssi': round(avg_rssi, 1) if avg_rssi else None
                })

            conn.close()

            coverage = {
                'antenna': {
                    'latitude': round(antenna_lat, 6),
                    'longitude': round(antenna_lon, 6),
                    'height_meters': round(antenna_height_m, 1),
                    'height_feet': round(antenna_height_ft, 0),
                    'confidence': 'high' if len(positions) > 20 else 'medium' if len(positions) > 10 else 'low',
                    'samples': len(all_positions)
                },
                'coverage_by_direction': coverage_by_direction
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(coverage, indent=2).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

    def serve_heatmap(self):
        """Serve heatmap data grouped by altitude slices"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # Define altitude ranges (in feet)
            altitude_ranges = [
                {'min': 0, 'max': 2000, 'label': '0-2,000 ft'},
                {'min': 2000, 'max': 5000, 'label': '2,000-5,000 ft'},
                {'min': 5000, 'max': 10000, 'label': '5,000-10,000 ft'},
                {'min': 10000, 'max': 20000, 'label': '10,000-20,000 ft'},
                {'min': 20000, 'max': 50000, 'label': '20,000+ ft'}
            ]

            heatmap_data = []

            for alt_range in altitude_ranges:
                # Get all positions within this altitude range
                cursor.execute('''
                    SELECT latitude, longitude, rssi, altitude
                    FROM signal_quality
                    WHERE latitude IS NOT NULL
                    AND longitude IS NOT NULL
                    AND rssi IS NOT NULL
                    AND altitude >= ?
                    AND altitude < ?
                ''', (alt_range['min'], alt_range['max']))

                points = cursor.fetchall()

                # Convert to list of dicts for JSON
                point_list = [
                    {
                        'lat': p[0],
                        'lon': p[1],
                        'rssi': p[2],
                        'altitude': p[3],
                        # Weight for heatmap (inverse of RSSI - stronger signal = higher weight)
                        'weight': max(0, 1.0 / (abs(p[2]) + 1))
                    }
                    for p in points
                ]

                heatmap_data.append({
                    'min_altitude': alt_range['min'],
                    'max_altitude': alt_range['max'],
                    'label': alt_range['label'],
                    'point_count': len(point_list),
                    'points': point_list
                })

            conn.close()

            response = {
                'altitude_ranges': heatmap_data,
                'total_points': sum(r['point_count'] for r in heatmap_data)
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def main():
    server = HTTPServer(('', PORT), LogAPIHandler)
    print("=" * 80)
    print(f"Flight Log API Server")
    print("=" * 80)
    print(f"Database: {DATABASE}")
    print(f"Listening on: http://localhost:{PORT}")
    print()
    print(f"API Endpoints:")
    print(f"  GET http://localhost:{PORT}/api/flights  - Get all flights")
    print(f"  GET http://localhost:{PORT}/api/stats    - Get statistics")
    print(f"  GET http://localhost:{PORT}/api/analytics- Get detailed analytics")
    print(f"  GET http://localhost:{PORT}/api/status   - Get system status")
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
