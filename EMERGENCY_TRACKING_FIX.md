# Emergency Tracking Fix - Deployment Guide

## Summary of Changes

Fixed emergency tracking to properly detect and categorize all emergency situations in the ADS-B tracker.

### What Was Wrong

**Previous Implementation:**
- Only checked dump1090's `emergency` field
- Didn't explicitly verify emergency squawk codes (7500, 7600, 7700)
- Didn't record the TYPE of emergency (hijacking, radio failure, etc.)
- Could miss emergencies that were only indicated by squawk codes

**Fixed Implementation:**
- Checks BOTH the `emergency` field AND squawk codes
- Properly categorizes emergency types:
  - **7500**: Aircraft Hijacking
  - **7600**: Radio Failure
  - **7700**: General Emergency
  - **ADS-B Emergency**: Other ADS-B priority status
- Stores emergency type in database for historical analysis
- Enhanced console alerts with specific emergency type

## Files Modified

1. **flight_logger_enhanced.py**
   - Added `EMERGENCY_SQUAWKS` mapping dictionary
   - Added `detect_emergency()` function for comprehensive detection
   - Updated `log_flight()` to use new detection logic
   - Updated `update_flight()` to preserve emergency type
   - Enhanced console output with specific emergency descriptions

2. **log_server.py**
   - Added `emergency_type` column to `/api/flights` endpoint
   - Added `emergency_type` column to `/api/analytics` endpoint
   - Emergency data now includes type information for frontend display

3. **add_emergency_type.py** (NEW)
   - Database migration script to add `emergency_type` column
   - Updates existing emergency records based on squawk codes

## Deployment Instructions

### Step 1: Stop Running Services on Raspberry Pi

```bash
ssh pi@your-raspberry-pi
cd ~/adsb-tracker
./stop_adsb_tracker.sh
```

### Step 2: Pull Latest Changes from GitHub

On your local machine:

```bash
cd ~/radioconda/Projects
git add -A
git commit -m "Fix emergency tracking: detect all emergency types and store classification"
git push origin main
```

On Raspberry Pi:

```bash
cd ~/adsb-tracker
git pull origin main
```

### Step 3: Run Database Migration

```bash
python3 add_emergency_type.py
```

Expected output:
```
======================================================================
DATABASE MIGRATION: Adding emergency_type column
======================================================================

✓ Added 'emergency_type' column to flights table
✓ Updated X existing emergency record(s) with emergency type

📊 Updated Flights Table Schema:
...
```

### Step 4: Restart Services

```bash
./start_adsb_tracker.sh
```

### Step 5: Verify Operation

Check that the services are running:

```bash
./check_status.sh
```

Monitor for emergency alerts:

```bash
tail -f ~/adsb-tracker/logs/flight_logger.log
```

When an emergency is detected, you should now see:
```
📝 New flight detected: UAL1234
  🚨 GENERAL EMERGENCY: Squawk 7700
```

## Testing Emergency Detection

To verify the fix is working:

1. **Check Emergency Events API:**
   ```bash
   curl http://localhost:8081/api/analytics | jq '.emergencies'
   ```

2. **View in Web Interface:**
   - Navigate to `http://your-pi:8080/stats.html`
   - Look for "Emergency Events" section
   - Emergency type should now be displayed

3. **Database Query:**
   ```bash
   sqlite3 ~/adsb-tracker/flight_log.db "SELECT callsign, squawk, emergency_type FROM flights WHERE emergency = 1 LIMIT 10;"
   ```

## Emergency Type Values

The `emergency_type` field will contain one of:

- `hijacking` - Squawk 7500 (Aircraft Hijacking)
- `radio_failure` - Squawk 7600 (Radio Failure)
- `general_emergency` - Squawk 7700 (General Emergency)
- `adsb_emergency` - ADS-B emergency flag set without special squawk
- `NULL` - No emergency (emergency = 0)

## Rollback Instructions

If you need to rollback:

```bash
cd ~/adsb-tracker
git checkout HEAD~1
./stop_adsb_tracker.sh
./start_adsb_tracker.sh
```

Note: The `emergency_type` column will remain in the database but will not be populated.

## Support

For questions or issues:
- Check logs: `~/adsb-tracker/logs/`
- Review status: `./check_status.sh`
- GitHub Issues: https://github.com/Cnd-North/adsb-flight-tracker/issues
