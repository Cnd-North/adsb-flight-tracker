#!/usr/bin/env python3
"""Test script to verify quota manager integration"""

import api_quota_manager as quota

print("=" * 60)
print("QUOTA MANAGER INTEGRATION TEST")
print("=" * 60)
print()

# Test 1: Check quota status
print("Test 1: Get quota status")
status = quota.get_quota_status()
print(f"  Month: {status['month']}")
print(f"  Used: {status['apis']['aviationstack']['used']}")
print(f"  Remaining: {status['apis']['aviationstack']['remaining']}")
print()

# Test 2: Check if we can make a request (priority airline)
print("Test 2: Check if we can make request (priority airline ACA123)")
can_request, msg = quota.can_make_request('aviationstack', 'ACA123')
print(f"  Can request: {can_request}")
print(f"  Message: {msg}")
print()

# Test 3: Check if we can make a request (non-priority airline)
print("Test 3: Check if we can make request (non-priority airline XYZ456)")
can_request, msg = quota.can_make_request('aviationstack', 'XYZ456')
print(f"  Can request: {can_request}")
print(f"  Message: {msg}")
print()

# Test 4: Priority airlines list
print("Test 4: Priority airlines")
print(f"  {', '.join(quota.PRIORITY_AIRLINES)}")
print()

print("=" * 60)
print("✓ Integration test complete")
print("=" * 60)
