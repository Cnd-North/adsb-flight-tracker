# 📡 ADS-B Hardware Guide

Complete guide to choosing and setting up hardware for your ADS-B tracking station.

---

## 🎯 Quick Recommendations by Budget

### Budget: $60-80 (Getting Started)
Perfect for apartment/condo dwellers or those wanting to test the hobby.

**What to buy:**
- RTL-SDR Blog V3 Dongle - $30
- Indoor 1090 MHz magnetic base antenna - $25
- Raspberry Pi Zero 2 W - $15
- microSD card (16GB) - $8

**Expected performance:**
- Range: 50-100 miles
- Aircraft tracked: 20-50 simultaneously
- Best for: Testing, urban areas, learning

---

### Enthusiast: $120-150 (Recommended)
Great balance of performance and cost for suburban homes.

**What to buy:**
- FlightAware Pro Stick Plus - $30
- Outdoor 1090 MHz collinear antenna - $40
- Raspberry Pi 4 (4GB) - $55
- 10ft LMR-400 coax cable - $15
- microSD card (32GB) - $10

**Expected performance:**
- Range: 150-250 miles
- Aircraft tracked: 50-150 simultaneously
- Best for: Most users, suburban/rural

---

### Pro: $200-300 (Maximum Performance)
For serious enthusiasts wanting the best possible reception.

**What to buy:**
- FlightAware Pro Stick Plus - $30
- High-gain outdoor collinear antenna (5-8 dBi) - $80
- Raspberry Pi 4 (8GB) - $75
- 25ft LMR-400 coax cable - $35
- Lightning arrestor - $25
- Antenna mast and mounting - $40
- microSD card (64GB) - $15

**Expected performance:**
- Range: 250-400+ miles
- Aircraft tracked: 150-300+ simultaneously
- Best for: Maximum coverage, feeders (FlightAware, FR24)

---

## 🔌 RTL-SDR Receivers

### FlightAware Pro Stick Plus ⭐ RECOMMENDED
- **Price:** ~$30
- **Pros:**
  - Built-in filter for 1090 MHz
  - Built-in LNA (low noise amplifier)
  - Optimized for ADS-B
  - Great documentation
- **Cons:**
  - Single-purpose (ADS-B only)
  - Slightly more expensive
- **Best for:** Dedicated ADS-B tracking
- [Buy on Amazon](https://www.amazon.com/s?k=flightaware+pro+stick&tag=electrobio-20) *

### RTL-SDR Blog V3
- **Price:** ~$30
- **Pros:**
  - General purpose (can do other SDR projects)
  - Built-in TCXO (temperature compensated oscillator)
  - Includes antennas
  - Great for learning
- **Cons:**
  - Needs external filter for best ADS-B performance
  - Slightly less sensitive than Pro Stick Plus
- **Best for:** Multi-purpose SDR, beginners
- [Buy on Amazon](https://www.amazon.com/s?k=rtl-sdr+blog+v3&tag=electrobio-20) *

### Generic RTL2832U Dongles
- **Price:** ~$15-25
- **Pros:**
  - Cheapest option
  - Works for testing
- **Cons:**
  - Lower quality
  - No built-in LNA or filter
  - Frequency drift
- **Best for:** Absolute budget builds only
- [Buy on Amazon](https://www.amazon.com/s?k=rtl2832u&tag=electrobio-20) *

---

## 📡 Antennas

### Indoor Antennas

#### Magnetic Base Desktop Antenna
- **Price:** ~$20-30
- **Range:** 50-100 miles
- **Pros:**
  - No installation required
  - Portable
  - Good for apartments
- **Cons:**
  - Limited range
  - Affected by buildings
- **Best for:** Urban apartments, testing
- [Buy on Amazon](https://www.amazon.com/s?k=1090+mhz+antenna+magnetic&tag=electrobio-20) *

#### Window-Mount Antenna
- **Price:** ~$30-40
- **Range:** 75-125 miles
- **Pros:**
  - Better than desktop
  - Minimal installation
  - Suction cup mount
- **Cons:**
  - Still limited by building
- **Best for:** High-rise apartments
- [Buy on Amazon](https://www.amazon.com/s?k=1090+mhz+antenna+window&tag=electrobio-20) *

### Outdoor Antennas ⭐ RECOMMENDED

#### Collinear Antenna (5 dBi)
- **Price:** ~$40-60
- **Range:** 150-250 miles
- **Pros:**
  - Excellent omnidirectional coverage
  - Weather-resistant
  - Professional results
- **Cons:**
  - Requires mounting
  - Needs coax cable
- **Best for:** Most users
- [Buy on Amazon](https://www.amazon.com/s?k=1090+mhz+collinear+antenna&tag=electrobio-20) *

#### High-Gain Collinear (8 dBi)
- **Price:** ~$80-120
- **Range:** 250-400 miles
- **Pros:**
  - Maximum range
  - Best performance
  - Commercial grade
- **Cons:**
  - Expensive
  - Requires good mounting
- **Best for:** Serious enthusiasts, feeders
- [Buy on Amazon](https://www.amazon.com/s?k=1090+mhz+antenna+8dbi&tag=electrobio-20) *

---

## 🔗 Coaxial Cable

### Cable Types

#### RG-6 (Budget)
- **Price:** ~$0.50/foot
- **Loss:** ~6 dB/100ft @ 1090 MHz
- **Best for:** Runs under 25 feet
- [Buy on Amazon](https://www.amazon.com/s?k=rg6+coax&tag=electrobio-20) *

#### LMR-240 (Good)
- **Price:** ~$1.00/foot
- **Loss:** ~4 dB/100ft @ 1090 MHz
- **Best for:** Runs 25-50 feet
- [Buy on Amazon](https://www.amazon.com/s?k=lmr-240&tag=electrobio-20) *

#### LMR-400 (Best) ⭐ RECOMMENDED
- **Price:** ~$1.50/foot
- **Loss:** ~2.5 dB/100ft @ 1090 MHz
- **Best for:** Runs over 50 feet, permanent installations
- [Buy on Amazon](https://www.amazon.com/s?k=lmr-400&tag=electrobio-20) *

### Cable Length Guidelines
- **Under 10 feet:** Use RG-6 (included cable is fine)
- **10-25 feet:** LMR-240 minimum
- **25-50 feet:** LMR-400 recommended
- **Over 50 feet:** LMR-400 required, consider adding an LNA

---

## 💻 Computer Options

### Raspberry Pi 4 (4GB) ⭐ RECOMMENDED
- **Price:** ~$55
- **Pros:**
  - Perfect performance for ADS-B
  - Low power (3-5W)
  - Compact
  - Easy to set up
- **Cons:**
  - Needs power supply, case, SD card
- **Best for:** Dedicated ADS-B station
- [Buy on Amazon](https://www.amazon.com/s?k=raspberry+pi+4&tag=electrobio-20) *

### Raspberry Pi Zero 2 W (Budget)
- **Price:** ~$15
- **Pros:**
  - Very cheap
  - Tiny
  - Low power (1-2W)
- **Cons:**
  - Limited to basic tracking (no analytics)
  - Single-core struggles with web interface
- **Best for:** Budget builds, indoor stations
- [Buy on Amazon](https://www.amazon.com/s?k=raspberry+pi+zero+2&tag=electrobio-20) *

### Existing PC/Mac
- **Price:** Free (use what you have)
- **Pros:**
  - Most powerful
  - Can run everything
  - Great for development
- **Cons:**
  - Higher power consumption
  - Not portable
- **Best for:** Testing, development, powerful analytics

### Intel NUC/Mini PC
- **Price:** ~$150-300
- **Pros:**
  - More powerful than Pi
  - x86 compatibility
  - Can run other services
- **Cons:**
  - More expensive
  - Higher power
- **Best for:** Multi-purpose home server
- [Buy on Amazon](https://www.amazon.com/s?k=intel+nuc&tag=electrobio-20) *

---

## ⚡ Accessories

### Power Supply
- Raspberry Pi: Official 5V 3A USB-C power supply - $8
- [Buy on Amazon](https://www.amazon.com/s?k=raspberry+pi+power+supply&tag=electrobio-20) *

### Storage
- **32GB microSD card** (minimum) - $8
- **64GB microSD card** (recommended) - $12
- Class 10 or better, A1 rating preferred
- [Buy on Amazon](https://www.amazon.com/s?k=microsd+64gb+a1&tag=electrobio-20) *

### Case
- **Official Raspberry Pi case** - $8
- **Passive cooling case** (aluminum) - $12
- **Active cooling case** (with fan) - $15
- [Buy on Amazon](https://www.amazon.com/s?k=raspberry+pi+4+case&tag=electrobio-20) *

### Lightning Protection ⚠️ IMPORTANT FOR OUTDOOR
- **Coax lightning arrestor** - $20-30
- Grounds RF to earth before entering house
- **Required for outdoor antennas**
- [Buy on Amazon](https://www.amazon.com/s?k=coax+lightning+arrestor&tag=electrobio-20) *

### Antenna Mounting
- **Chimney mount** - $25-40
- **Pole mount** - $15-25
- **Attic/wall mount** - $10-20
- [Buy on Amazon](https://www.amazon.com/s?k=antenna+mount&tag=electrobio-20) *

---

## 📐 Antenna Placement Tips

### Height Matters
- **Every 10 feet of height ≈ 10 miles of range**
- Rooftop > Attic > Window > Desktop

### Clear Line of Sight
- Minimize obstacles between antenna and aircraft
- Trees, buildings, hills block signals
- Even attic installations work well

### Avoid Interference
- Keep away from:
  - Power lines
  - Other antennas (TV, cell, Wi-Fi)
  - Metal roofs
  - Solar panels

### Grounding (Outdoor Installations)
- **Always ground outdoor antennas**
- Use lightning arrestor
- Follow local electrical codes
- Consider hiring electrician for mast grounding

---

## 🛠️ Installation Examples

### Budget Desktop Setup ($65)
```
RTL-SDR Blog V3 ($30)
  ↓ [included 3ft cable]
Magnetic base antenna ($25)
  → on desk

Raspberry Pi Zero 2 W ($15)
+ Power supply ($5)
+ 16GB microSD ($5)
```
**Total: $65**
**Range: 50-100 miles**

### Recommended Outdoor Setup ($145)
```
FlightAware Pro Stick Plus ($30)
  ↓ [10ft LMR-400 cable ($15)]
Outdoor collinear antenna ($40)
  → mounted on chimney ($25)

Raspberry Pi 4 4GB ($55)
+ Power supply ($8)
+ Case ($8)
+ 32GB microSD ($8)
```
**Total: $145 (excluding mount)**
**Range: 150-250 miles**

### Pro Installation ($285)
```
FlightAware Pro Stick Plus ($30)
  ↓ [25ft LMR-400 ($35)]
Lightning arrestor ($25)
  ↓ [6ft jumper cable]
High-gain collinear 8dBi ($80)
  → 10ft mast on roof ($40)

Raspberry Pi 4 8GB ($75)
+ Power supply ($8)
+ Aluminum case ($12)
+ 64GB microSD ($12)
```
**Total: $285 (excluding mast mounting)**
**Range: 250-400+ miles**

---

## 📊 Expected Performance

### Typical Results by Setup

| Setup | Range (miles) | Aircraft Count | Cost |
|-------|---------------|----------------|------|
| Budget Indoor | 50-100 | 10-30 | $60 |
| Standard Outdoor | 150-250 | 50-150 | $120 |
| Pro Outdoor | 250-400+ | 150-300+ | $250 |

*Results vary by location, elevation, and local geography*

### Factors Affecting Range

✅ **Increases Range:**
- Higher antenna placement
- Better antenna (collinear > dipole)
- Low-loss coax cable
- LNA (low noise amplifier)
- Clear line of sight
- Higher elevation location

❌ **Decreases Range:**
- Obstacles (buildings, trees, hills)
- Poor quality cable
- Indoor installation
- Interference sources
- Low elevation location

---

## 🎓 Pro Tips

1. **Start Simple**
   - Begin with budget setup
   - Upgrade antenna first, then cable, then receiver

2. **Test Before Installing**
   - Run desktop setup for a week
   - Understand what you're tracking
   - Then plan outdoor installation

3. **Cable Matters**
   - Every foot of cheap cable = lost range
   - LMR-400 is worth the investment
   - Keep runs as short as possible

4. **Community Feeding**
   - Feed FlightAware, FR24, ADSB Exchange
   - Get free premium accounts
   - Share data, help the community

5. **Weather-Proof Everything**
   - Use outdoor-rated connectors
   - Weatherproof tape on all connections
   - Check connections after storms

---

## 🔗 Useful Resources

- **FlightAware Forums:** https://discussions.flightaware.com/
- **RTL-SDR Blog:** https://www.rtl-sdr.com/
- **ADS-B Exchange Forums:** https://www.adsbexchange.com/forums/
- **Reddit:** r/ADSB, r/RTLSDR

---

\* *Amazon affiliate links help support this project at no extra cost to you. Thank you!*

**Questions?** Open an issue on GitHub or join the discussions!
