#!/usr/bin/env python3
"""
API Quota Manager
Tracks and limits API usage to stay within monthly quotas
"""

import json
import os
from datetime import datetime

QUOTA_FILE = os.path.expanduser("~/adsb-tracker/.api_quota.json")

# Monthly quotas for each API
QUOTAS = {
    'aviationstack': 100,  # Free tier: 100 requests/month
}

# Priority airlines (worth spending API quota on)
PRIORITY_AIRLINES = [
    'ACA',  # Air Canada
    'WJA', 'WEN',  # WestJet
    'UAL',  # United
    'DAL',  # Delta
    'AAL',  # American
    'ASA',  # Alaska
    'JBU',  # JetBlue
]

def load_quota_data():
    """Load quota tracking data from file"""
    if not os.path.exists(QUOTA_FILE):
        return {
            'month': datetime.now().strftime('%Y-%m'),
            'aviationstack': 0
        }

    try:
        with open(QUOTA_FILE, 'r') as f:
            data = json.load(f)

            # Reset if new month
            current_month = datetime.now().strftime('%Y-%m')
            if data.get('month') != current_month:
                return {
                    'month': current_month,
                    'aviationstack': 0
                }

            return data
    except:
        return {
            'month': datetime.now().strftime('%Y-%m'),
            'aviationstack': 0
        }

def save_quota_data(data):
    """Save quota tracking data to file"""
    try:
        with open(QUOTA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save quota data: {e}")

def get_remaining_quota(api_name='aviationstack'):
    """Get remaining quota for an API"""
    data = load_quota_data()
    used = data.get(api_name, 0)
    total = QUOTAS.get(api_name, 0)
    return total - used

def can_make_request(api_name='aviationstack', callsign=None):
    """Check if we can make an API request"""
    remaining = get_remaining_quota(api_name)

    if remaining <= 0:
        return False, f"Monthly quota exhausted (0/{QUOTAS[api_name]} remaining)"

    # Warn when low
    if remaining <= 10:
        print(f"⚠️  Low quota: {remaining}/{QUOTAS[api_name]} requests remaining this month")

    # Prioritize certain airlines when quota is limited
    if remaining <= 20 and callsign:
        # Check if this is a priority airline
        is_priority = any(callsign.startswith(prefix) for prefix in PRIORITY_AIRLINES)
        if not is_priority:
            return False, f"Saving quota for priority airlines ({remaining} remaining)"

    return True, f"OK ({remaining}/{QUOTAS[api_name]} remaining)"

def record_request(api_name='aviationstack', success=True):
    """Record that an API request was made"""
    data = load_quota_data()
    data[api_name] = data.get(api_name, 0) + 1
    save_quota_data(data)

    remaining = get_remaining_quota(api_name)
    return remaining

def get_quota_status():
    """Get current quota status for all APIs"""
    data = load_quota_data()
    status = {
        'month': data.get('month'),
        'apis': {}
    }

    for api_name, total in QUOTAS.items():
        used = data.get(api_name, 0)
        remaining = total - used
        status['apis'][api_name] = {
            'used': used,
            'total': total,
            'remaining': remaining,
            'percentage': round((used / total * 100) if total > 0 else 0, 1)
        }

    return status

def print_quota_status():
    """Print quota status for all APIs"""
    status = get_quota_status()

    print("=" * 60)
    print("API QUOTA STATUS")
    print("=" * 60)
    print(f"Month: {status['month']}")
    print()

    for api_name, stats in status['apis'].items():
        print(f"{api_name.upper()}:")
        print(f"  Used:      {stats['used']}/{stats['total']} ({stats['percentage']}%)")
        print(f"  Remaining: {stats['remaining']}")

        # Progress bar
        bar_length = 40
        filled = int(bar_length * stats['used'] / stats['total'])
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  [{bar}]")

        # Warnings
        if stats['remaining'] == 0:
            print(f"  ⚠️  QUOTA EXHAUSTED - Resets next month")
        elif stats['remaining'] <= 10:
            print(f"  ⚠️  LOW QUOTA - {stats['remaining']} requests left")
        print()

    print("=" * 60)

if __name__ == "__main__":
    print_quota_status()
