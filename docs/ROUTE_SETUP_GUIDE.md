# Live Route Data Setup Guide

Your enhanced flight logger now captures **live route information** for new flights!

---

## 🎯 How It Works

When a new flight is detected, the logger automatically:
1. ✅ Gets aircraft details from OpenSky Network (free, no key needed)
2. 🛫 Queries **live flight APIs** for current route information
3. 💾 Saves origin → destination airports to database

---

## 📡 API Sources (in order of priority)

### 1. Aviation Stack API (Optional - Recommended)

**Status:** Optional but gives best results
**Cost:** FREE (100 requests/month)
**Coverage:** Commercial flights with flight numbers

#### Setup Steps:

```bash
# 1. Sign up for free account
open https://aviationstack.com/product

# 2. After signup, get your API key from dashboard
# 3. Set environment variable
export AVIATIONSTACK_KEY='your-api-key-here'

# 4. Restart the logger
~/radioconda/Projects/stop_adsb.sh
~/radioconda/Projects/start_adsb.sh
```

#### Add to Shell Profile (Permanent):

```bash
# Add to ~/.zshrc or ~/.bashrc
echo "export AVIATIONSTACK_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

### 2. ADS-B Exchange API (Automatic)

**Status:** Always active (no key needed)
**Cost:** FREE (limited)
**Coverage:** Some flights, rate limited

This is used automatically as a fallback. No setup required!

---

## ✅ Verify Setup

Check if Aviation Stack key is configured:

```bash
# Should show your API key
echo $AVIATIONSTACK_KEY

# Check logger status
ps aux | grep flight_logger_enhanced
tail -f ~/radioconda/Projects/flight_logger.log
```

---

## 🎮 Testing Route Capture

Wait for a new flight to be detected. You should see:

```
📝 New flight detected: ACA549
  ✈️  Registration: C-XXXX
  🏭 Boeing 737-MAX
  🏢 Operator: Air Canada
  🛫 Route (AviationStack): YYZ → YVR  ← NEW!
```

---

## 📊 View Routes in Web Interface

**Statistics Page:** http://localhost:8080/stats.html
- Click on operators/models to see routes
- Routes shown as "YYZ → YVR" format

**Flight Log:** http://localhost:8080/log.html
- Route column now populated for new flights

---

## ⚠️ Important Notes

### API Rate Limits

**Aviation Stack FREE tier:**
- 100 requests/month
- ~3 flights per day
- Choose wisely!

**Strategy:**
- Logger only queries for flights with callsigns
- Results are cached to avoid duplicates
- Monitor your usage at: https://aviationstack.com/dashboard

### Historical Data

❌ **Existing flights:** Cannot backfill routes (APIs don't provide historical data)
✅ **New flights:** Will capture routes automatically from now on

### When Routes Won't Be Found

Routes may be unavailable for:
- ✈️ Private aircraft (no flight plans published)
- 🚁 Helicopters (often don't file commercial routes)
- 🛩️ Military aircraft (routes not public)
- 📡 Aircraft without callsigns
- 🌐 Flights not in API databases

---

## 🔧 Troubleshooting

### "No route data available"

This is normal! Not all flights have public route data. The logger will:
- Still log the flight
- Save all other data (manufacturer, operator, etc.)
- Just leave route fields empty

### API errors

```bash
# Check API key is set
echo $AVIATIONSTACK_KEY

# Test API manually
curl "http://api.aviationstack.com/v1/flights?access_key=YOUR_KEY&limit=1"
```

### Logger not calling APIs

Make sure you:
1. Restarted the logger after setting API key
2. Have new flights with callsigns (not just ICAO)
3. Check logger output: `tail -f ~/radioconda/Projects/flight_logger.log`

---

## 📈 Expected Results

**With Aviation Stack API:**
- ~70-80% route capture for commercial flights
- Major airlines (Air Canada, WestJet, etc.) covered
- Regional flights may vary

**Without API key (ADS-B Exchange only):**
- ~10-20% route capture
- Hit or miss, but free!

---

## 💡 Alternative: Premium Options

If you need comprehensive route data:

1. **FlightAware AeroAPI**
   - Cost: $50-200/month
   - Coverage: 95%+ of flights
   - Historical data available

2. **FlightRadar24 Business**
   - Cost: ~€500/month
   - Real-time + historical

For hobby use, the free APIs are usually sufficient! 🎉

---

## Quick Reference

| Task | Command |
|------|---------|
| **Set API key** | `export AVIATIONSTACK_KEY='key'` |
| **Check key** | `echo $AVIATIONSTACK_KEY` |
| **Restart logger** | `~/radioconda/Projects/stop_adsb.sh && ~/radioconda/Projects/start_adsb.sh` |
| **View log** | `tail -f ~/radioconda/Projects/flight_logger.log` |
| **Check usage** | Visit https://aviationstack.com/dashboard |

---

Happy flight tracking with routes! ✈️ 🗺️
