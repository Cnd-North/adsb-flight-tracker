#!/usr/bin/env python3
"""Analyze storage requirements for signal quality data"""

import sys

def calculate_storage():
    """Calculate storage requirements for different sampling rates"""

    print("=" * 70)
    print("SIGNAL QUALITY DATA - STORAGE ANALYSIS")
    print("=" * 70)
    print()

    # Assumptions
    avg_aircraft = 10  # Average aircraft tracked simultaneously
    bytes_per_record = 100  # Conservative estimate per signal sample

    print("📊 Assumptions:")
    print(f"  • Average aircraft tracked: {avg_aircraft}")
    print(f"  • Bytes per record: {bytes_per_record}")
    print()

    # Storage per record breakdown
    print("📦 Data per record:")
    print("  • ICAO (4 bytes) + timestamp (8 bytes)")
    print("  • RSSI/signal strength (4 bytes)")
    print("  • Lat/Lon (8 bytes each)")
    print("  • Altitude (4 bytes)")
    print("  • Distance (4 bytes)")
    print("  • Messages count (4 bytes)")
    print("  • Overhead (indexes, etc): ~60 bytes")
    print(f"  • Total: ~{bytes_per_record} bytes")
    print()

    scenarios = [
        ("Every 1 second", 1),
        ("Every 5 seconds", 5),
        ("Every 10 seconds", 10),
        ("Every 30 seconds", 30),
        ("Every 60 seconds", 60),
    ]

    print("=" * 70)
    print("STORAGE REQUIREMENTS")
    print("=" * 70)
    print()

    for name, interval in scenarios:
        samples_per_hour = 3600 / interval
        records_per_hour = avg_aircraft * samples_per_hour

        bytes_per_hour = records_per_hour * bytes_per_record
        mb_per_hour = bytes_per_hour / (1024 * 1024)
        mb_per_day = mb_per_hour * 24
        gb_per_month = (mb_per_day * 30) / 1024
        gb_per_year = gb_per_month * 12

        print(f"📍 {name}:")
        print(f"  Per hour:  {mb_per_hour:,.1f} MB")
        print(f"  Per day:   {mb_per_day:,.1f} MB")
        print(f"  Per month: {gb_per_month:,.2f} GB")
        print(f"  Per year:  {gb_per_year:,.2f} GB")
        print()

    print("=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    print()

    print("✅ BEST OPTION: 10-second intervals")
    print("  • ~8.6 MB/day (~260 MB/month)")
    print("  • Captures all important signal variations")
    print("  • Still detailed enough for analysis")
    print("  • Very manageable storage")
    print()

    print("📈 OPTIMIZATION STRATEGIES:")
    print()
    print("1. Tiered Retention:")
    print("  • Keep 10-sec data for 7 days (~60 MB)")
    print("  • Aggregate to 1-min averages for 30 days (~52 MB)")
    print("  • Keep hourly stats forever (minimal space)")
    print("  • Total: ~112 MB + yearly stats")
    print()

    print("2. Smart Sampling:")
    print("  • Only log when signal changes >3 dB")
    print("  • Reduces storage by 50-70%")
    print("  • Still captures all important events")
    print()

    print("3. Compression:")
    print("  • SQLite VACUUM can reduce size 20-30%")
    print("  • Store aggregated stats instead of raw samples")
    print()

    print("=" * 70)
    print("🎯 ANALYSIS CAPABILITIES")
    print("=" * 70)
    print()

    print("With this data, you can analyze:")
    print()
    print("📍 Antenna Performance:")
    print("  • Signal strength by direction (N/S/E/W)")
    print("  • Coverage patterns (heatmaps)")
    print("  • Blind spots identification")
    print()

    print("✈️ Aircraft Characteristics:")
    print("  • Which aircraft types have strongest signals")
    print("  • Commercial vs private signal differences")
    print("  • Altitude vs signal strength correlation")
    print()

    print("🕐 Time-of-Day Patterns:")
    print("  • Sunrise/sunset signal degradation")
    print("  • Hourly signal quality trends")
    print("  • Peak performance times")
    print()

    print("📏 Distance Analysis:")
    print("  • Maximum detection range by direction")
    print("  • Signal strength vs distance curves")
    print("  • Identify atmospheric ducting events")
    print()

    print("🌤️ Weather Correlation:")
    print("  • Signal quality vs time (match with weather data)")
    print("  • Temperature inversion effects")
    print("  • Precipitation impact")
    print()

if __name__ == "__main__":
    calculate_storage()
