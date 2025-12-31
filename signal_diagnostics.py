#!/usr/bin/env python3
"""ADS-B Signal Diagnostics Tool"""

import requests
import json
import time
from datetime import datetime
import sys

DUMP1090_URL = "http://localhost:8080/data/aircraft.json"

def get_signal_data():
    """Fetch current signal data from dump1090"""
    try:
        response = requests.get(DUMP1090_URL, timeout=5)
        return response.json()
    except Exception as e:
        print(f"❌ Error connecting to dump1090: {e}")
        return None

def analyze_signal(data):
    """Analyze signal quality and provide diagnostics"""
    if not data:
        return None

    aircraft = data.get('aircraft', [])
    messages = data.get('messages', 0)

    # Count aircraft by signal strength
    strong_signal = []  # > -10 dBFS
    good_signal = []    # -10 to -20 dBFS
    weak_signal = []    # -20 to -30 dBFS
    poor_signal = []    # < -30 dBFS
    no_rssi = []

    for a in aircraft:
        rssi = a.get('rssi')
        if rssi is None:
            no_rssi.append(a)
        elif rssi > -10:
            strong_signal.append(a)
        elif rssi > -20:
            good_signal.append(a)
        elif rssi > -30:
            weak_signal.append(a)
        else:
            poor_signal.append(a)

    # Calculate average signal strength
    signals = [a.get('rssi', -40) for a in aircraft if a.get('rssi') is not None]
    avg_signal = sum(signals) / len(signals) if signals else -40

    # Count position updates
    recent_positions = [a for a in aircraft if a.get('seen_pos', 999) < 5]

    return {
        'total_aircraft': len(aircraft),
        'messages': messages,
        'strong_signal': len(strong_signal),
        'good_signal': len(good_signal),
        'weak_signal': len(weak_signal),
        'poor_signal': len(poor_signal),
        'no_rssi': len(no_rssi),
        'avg_signal': avg_signal,
        'recent_positions': len(recent_positions),
        'aircraft_with_positions': [a for a in aircraft if 'lat' in a and 'lon' in a]
    }

def print_diagnostics(stats, prev_stats=None):
    """Print diagnostic information"""
    print("\n" + "=" * 70)
    print(f"📡 ADS-B SIGNAL DIAGNOSTICS - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)

    if stats['total_aircraft'] == 0:
        print("\n❌ CRITICAL: NO AIRCRAFT DETECTED")
        print("\nPossible causes:")
        print("  1. Antenna disconnected or damaged")
        print("  2. dump1090 not receiving data from SDR")
        print("  3. SDR device not connected/powered")
        print("  4. Atmospheric conditions (unlikely to affect ALL signals)")
        print("  5. Interference from nearby electronics")
        print("\nTroubleshooting steps:")
        print("  • Check antenna connection")
        print("  • Restart dump1090: pkill dump1090 && dump1090 --net")
        print("  • Check SDR device: lsusb | grep RTL")
        print("  • Try moving antenna away from electronics")
        return

    print(f"\n✈️  Aircraft Tracked: {stats['total_aircraft']}")
    print(f"📨 Total Messages: {stats['messages']}")
    print(f"📍 Recent Positions: {stats['recent_positions']}")
    print(f"📊 Average Signal: {stats['avg_signal']:.1f} dBFS")

    print("\n📶 Signal Distribution:")
    print(f"  🟢 Strong (>-10 dBFS):  {stats['strong_signal']}")
    print(f"  🟡 Good (-10 to -20):   {stats['good_signal']}")
    print(f"  🟠 Weak (-20 to -30):   {stats['weak_signal']}")
    print(f"  🔴 Poor (<-30 dBFS):    {stats['poor_signal']}")
    print(f"  ⚪ No RSSI data:        {stats['no_rssi']}")

    # Diagnose issues
    print("\n🔍 DIAGNOSIS:")

    if stats['total_aircraft'] < 5:
        print("  ⚠️  Low aircraft count - signal may be degraded")
        print("     • Check antenna position (should be outdoors, elevated)")
        print("     • Check for nearby interference sources")
        print("     • Weather conditions may be affecting propagation")

    if stats['avg_signal'] < -25:
        print("  ⚠️  Weak average signal strength")
        print("     • Antenna may need repositioning")
        print("     • Check cable connections for corrosion/damage")
        print("     • Consider using a higher-gain antenna")
        print("     • Check for water ingress in antenna/connectors")

    if stats['poor_signal'] > stats['good_signal']:
        print("  ⚠️  More poor signals than good signals")
        print("     • Antenna gain may be insufficient")
        print("     • Cable loss may be too high (check cable length/quality)")
        print("     • LNA (low-noise amplifier) may help if >50ft cable")

    if stats['recent_positions'] < stats['total_aircraft'] * 0.5:
        print("  ⚠️  Low position update rate")
        print("     • Some aircraft may be too far or blocked")
        print("     • Signal quality may be marginal")

    # Compare with previous reading
    if prev_stats:
        aircraft_change = stats['total_aircraft'] - prev_stats['total_aircraft']
        signal_change = stats['avg_signal'] - prev_stats['avg_signal']

        if aircraft_change < -5:
            print(f"  📉 Aircraft count dropped by {abs(aircraft_change)}")
            print("     • Sudden atmospheric change (temperature inversion)")
            print("     • Time of day effects (sunrise/sunset)")
            print("     • Local interference started")

        if signal_change < -5:
            print(f"  📉 Signal strength dropped by {abs(signal_change):.1f} dB")
            print("     • Check antenna connections")
            print("     • Possible water ingress")
            print("     • SDR may be overheating")

    # Environmental factors
    print("\n🌤️  ENVIRONMENTAL FACTORS:")
    hour = datetime.now().hour
    if 5 <= hour <= 8:
        print("  ☀️  Sunrise period - temperature inversions can affect signal")
        print("     • Atmospheric ducting changes")
        print("     • Solar noise increases")
        print("     • Normal to see reduced range during sunrise")
    elif 17 <= hour <= 20:
        print("  🌅 Sunset period - atmospheric changes expected")
        print("     • Temperature inversions forming")
        print("     • Normal to see signal variations")

    if stats['total_aircraft'] > 0:
        print("\n✅ Overall: System is receiving signals")
        if stats['avg_signal'] > -20 and stats['total_aircraft'] > 10:
            print("   Signal quality is GOOD")
        elif stats['avg_signal'] > -25 and stats['total_aircraft'] > 5:
            print("   Signal quality is ACCEPTABLE")
        else:
            print("   Signal quality could be improved")

def monitor_mode(interval=10):
    """Continuous monitoring mode"""
    print("Starting continuous monitoring (Ctrl+C to stop)...")
    print(f"Update interval: {interval} seconds\n")

    prev_stats = None
    try:
        while True:
            data = get_signal_data()
            if data:
                stats = analyze_signal(data)
                print_diagnostics(stats, prev_stats)
                prev_stats = stats
            else:
                print("\n❌ Cannot connect to dump1090")
                print("   • Is dump1090 running?")
                print("   • Check: lsof -i :8080")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

def single_check():
    """Single diagnostic check"""
    data = get_signal_data()
    if data:
        stats = analyze_signal(data)
        print_diagnostics(stats)

        # Show some aircraft details
        if stats['aircraft_with_positions']:
            print("\n📍 Aircraft with Position Data:")
            for i, aircraft in enumerate(stats['aircraft_with_positions'][:5], 1):
                reg = aircraft.get('flight', aircraft.get('hex', 'Unknown')).strip()
                alt = aircraft.get('alt_baro', 'N/A')
                rssi = aircraft.get('rssi', 'N/A')
                dist = aircraft.get('distance', 'N/A')
                print(f"  {i}. {reg:12s} Alt: {str(alt):>6s} ft  "
                      f"RSSI: {str(rssi):>6s} dBFS")
            if len(stats['aircraft_with_positions']) > 5:
                print(f"  ... and {len(stats['aircraft_with_positions']) - 5} more")
    else:
        print("\n❌ Cannot connect to dump1090 - is it running?")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        monitor_mode(interval)
    else:
        single_check()
