# API Quota Management System

## Overview

The quota management system prevents your ADS-B tracker from exceeding the 100 requests/month limit on the free Aviation Stack API tier.

## How It Works

### 1. Automatic Tracking
- Every API request is automatically tracked in `~/.api_quota.json`
- The quota counter **resets automatically** on the first day of each month
- You don't need to manually manage anything

### 2. Smart Request Limits

**When you have 96+ requests remaining:**
- All flights with callsigns will query Aviation Stack for route data

**When you have 20 or fewer requests remaining:**
- Only **priority airlines** will use API quota
- Other flights will skip Aviation Stack and try free alternatives (ADS-B Exchange)

**When quota is exhausted (0 remaining):**
- All Aviation Stack requests are blocked
- Free alternatives are still used (ADS-B Exchange)

### 3. Priority Airlines

These airlines are considered high-value and will continue to use API quota even when running low:

- **ACA** - Air Canada
- **WJA**, **WEN** - WestJet
- **UAL** - United
- **DAL** - Delta
- **AAL** - American
- **ASA** - Alaska
- **JBU** - JetBlue

**To customize:** Edit the `PRIORITY_AIRLINES` list in `api_quota_manager.py`

## Monitoring Your Quota

### Check Current Status

Run the quota status command:
```bash
python3 ~/radioconda/Projects/api_quota_manager.py
```

Output example:
```
============================================================
API QUOTA STATUS
============================================================
Month: 2025-12

AVIATIONSTACK:
  Used:      4/100 (4.0%)
  Remaining: 96
  [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]

============================================================
```

### In the Flight Logger

The logger displays quota status when it starts:
```
📡 Route Data Sources:
  ✓ Aviation Stack API: 96/100 requests remaining (4 used)
```

And when a route is captured:
```
📝 New flight detected: ACA123
  🛫 Route (AviationStack): YYZ → YVR
  📊 API quota: 95 requests remaining this month
```

## What Gets Tracked

The quota file (`~/.api_quota.json`) contains:
```json
{
  "month": "2025-12",
  "aviationstack": 4
}
```

- **month**: Current tracking period (YYYY-MM format)
- **aviationstack**: Number of API calls made this month

## Troubleshooting

### "Skipping API call: Saving quota for priority airlines"

This means:
- You have 20 or fewer requests remaining
- The current flight is not a priority airline
- The system is conserving quota for more important flights

**Solution:** Either wait for the month to reset, or add the airline to the priority list

### "Skipping API call: Monthly quota exhausted"

This means:
- You've used all 100 requests this month
- Quota will reset on the 1st of next month

**Solution:**
1. Wait for monthly reset (automatic)
2. Upgrade to paid Aviation Stack tier
3. Rely on free alternatives (ADS-B Exchange)

### Check Quota File

```bash
cat ~/.api_quota.json
```

### Manually Reset Quota (for testing only)

```bash
rm ~/.api_quota.json
```

**Warning:** This resets your usage counter. Only use for testing!

## Expected Coverage

With 100 requests/month and smart quota management:

- **High traffic areas (10-20 flights/day):** ~5-10 days of full coverage, then priority-only
- **Medium traffic (5-10 flights/day):** ~10-20 days of full coverage
- **Low traffic (1-5 flights/day):** Full month coverage

The system automatically optimizes to spread coverage across the entire month.

## Upgrading Your Plan

If you need more than 100 requests/month:

1. Visit https://aviationstack.com/product
2. Choose a paid plan (500-10,000 requests/month)
3. Update your API key: `export AVIATIONSTACK_KEY='new-key'`
4. Edit quota limit in `api_quota_manager.py`:
   ```python
   QUOTAS = {
       'aviationstack': 500,  # Update this number
   }
   ```

## Files in the System

- **api_quota_manager.py** - Core quota tracking logic
- **flight_logger_enhanced.py** - Flight logger with quota integration
- **~/.api_quota.json** - Quota tracking data (auto-created)

## Summary

✓ Automatic monthly quota tracking
✓ Smart priority-based request filtering
✓ Real-time quota status display
✓ No manual intervention required
✓ Prevents API overages

The system is fully automatic - just start the logger and it handles everything!
