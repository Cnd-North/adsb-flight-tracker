# Contributing to ADS-B Flight Tracker Pro

First off, thank you for considering contributing! ✈️

This project is built by aviation enthusiasts for aviation enthusiasts. We welcome contributions of all kinds.

## 🎯 Ways to Contribute

### 1. 🐛 Report Bugs
Found a bug? Help us fix it!

- Check if the bug has already been reported in [Issues](https://github.com/Cnd-North/adsb-flight-tracker/issues)
- If not, open a new issue with:
  - Clear, descriptive title
  - Detailed description of the problem
  - Steps to reproduce
  - Expected vs actual behavior
  - Your environment (OS, Python version, hardware)
  - Relevant logs or screenshots

### 2. 💡 Suggest Features
Have an idea? We'd love to hear it!

- Check existing [Feature Requests](https://github.com/Cnd-North/adsb-flight-tracker/issues?q=label%3Aenhancement)
- Open a new issue with:
  - Clear description of the feature
  - Why it would be useful
  - How it might work
  - Any implementation ideas

### 3. 🔧 Submit Pull Requests

#### Quick Changes (Typos, Docs)
For small fixes, just:
1. Fork the repo
2. Make your change
3. Submit a PR

#### Code Changes
For code changes:

1. **Fork and Clone**
   ```bash
   git clone https://github.com/Cnd-North/adsb-flight-tracker.git
   cd adsb-flight-tracker
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Write clear, commented code
   - Follow existing code style
   - Test your changes thoroughly
   - Update documentation if needed

4. **Test**
   ```bash
   # Test imports
   python -c "import route_optimizer"
   python -c "import api_quota_manager"

   # Run any existing tests
   python route_optimizer.py
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

   Use clear commit messages:
   - `Add feature: intelligent route caching`
   - `Fix: database connection timeout`
   - `Update: README with new hardware guide`
   - `Docs: improve setup instructions`

6. **Push and PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub!

### 4. 📖 Improve Documentation

Documentation is crucial! Help us make it better:

- Fix typos and grammar
- Add examples
- Clarify confusing sections
- Translate to other languages
- Add troubleshooting tips
- Create tutorials or guides

### 5. 🧪 Test and Provide Feedback

- Test new features
- Try different hardware setups
- Report what works (and what doesn't)
- Share your configuration
- Post screenshots or videos

---

## 📝 Code Style Guidelines

### Python Code
- **PEP 8 compliant** (mostly - be reasonable)
- **4 spaces for indentation** (no tabs)
- **Clear variable names** (no single letters except loop counters)
- **Comment complex logic**
- **Docstrings for functions**

Example:
```python
def calculate_priority_score(callsign, icao, registration=None):
    """
    Calculate priority score for API call.

    Args:
        callsign: Aircraft callsign (e.g., 'UAL123')
        icao: Aircraft ICAO hex code (e.g., 'A12345')
        registration: Optional aircraft registration (e.g., 'N12345')

    Returns:
        tuple: (score, reasons) where score is int and reasons is list of str
    """
    # Implementation...
```

### JavaScript/HTML
- **2 spaces for indentation**
- **Semicolons required**
- **camelCase for variables**
- **Clear function names**

### Markdown
- **Use headers hierarchically** (H1 → H2 → H3)
- **Code blocks with language tags**
- **Lists for multiple items**
- **Links with descriptive text**

---

## 🏗️ Project Structure

```
adsb-flight-tracker/
├── Core Python Scripts
│   ├── flight_logger_enhanced.py    # Main logger
│   ├── route_optimizer.py           # Route prioritization
│   ├── api_quota_manager.py         # Quota management
│   └── log_server.py                # REST API
│
├── Setup & Utilities
│   ├── setup_database.py            # DB initialization
│   ├── normalize_manufacturers.py   # Data quality
│   └── fix_corrupted_aircraft.py    # Data cleanup
│
├── Web Interface
│   └── dump1090-fa-web/public_html/
│       ├── index.html               # Live map
│       ├── stats.html               # Statistics
│       ├── log.html                 # Flight log
│       └── signal-monitor.html      # Signal quality
│
├── Documentation
│   ├── README.md                    # Main docs
│   ├── HARDWARE_GUIDE.md            # Hardware help
│   ├── ROUTE_SETUP_GUIDE.md         # API setup
│   └── CONTRIBUTING.md              # This file
│
└── GitHub
    ├── .github/workflows/           # CI/CD
    ├── .gitignore                   # Git excludes
    └── LICENSE                      # MIT License
```

---

## 🎯 Feature Areas Needing Help

### High Priority
- [ ] Support for additional route APIs (FlightAware, OpenSky)
- [ ] Better error handling and recovery
- [ ] Unit tests for core functions
- [ ] Docker container setup
- [ ] Automatic software updates

### Medium Priority
- [ ] Mobile-responsive web interface
- [ ] Email/push notifications for interesting aircraft
- [ ] Export to KML/GPX formats
- [ ] Integration with home automation (Home Assistant)
- [ ] Multi-receiver support (merge data from multiple dongles)

### Nice to Have
- [ ] Dark mode for web interface
- [ ] Custom alerts (altitude, speed, squawk codes)
- [ ] Historical replay of tracked flights
- [ ] 3D visualization of flight paths
- [ ] AI-powered aircraft type identification

---

## 🧪 Testing Guidelines

### Before Submitting PR

1. **Test manually** with your hardware
2. **Check imports** don't break
3. **Verify database changes** work correctly
4. **Test web interface** in multiple browsers
5. **Update docs** if you changed functionality

### Helpful Test Commands

```bash
# Test Python syntax
python -m py_compile *.py

# Test imports
python -c "import route_optimizer; import api_quota_manager"

# Test route optimizer
python route_optimizer.py

# Check database
sqlite3 flight_log.db "SELECT COUNT(*) FROM flights;"

# Test web interface
python3 -m http.server 8080
```

---

## 📋 Pull Request Checklist

Before submitting your PR, make sure:

- [ ] Code follows style guidelines
- [ ] Changes are tested and working
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] PR description explains the change
- [ ] Screenshots included (for UI changes)

---

## 🤝 Code of Conduct

### Our Standards

- ✅ Be respectful and welcoming
- ✅ Provide constructive feedback
- ✅ Focus on what's best for the community
- ✅ Show empathy toward others
- ✅ Accept constructive criticism gracefully

- ❌ No harassment or trolling
- ❌ No personal attacks
- ❌ No publishing others' private info
- ❌ No spam or self-promotion

### Enforcement

Violations may result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report issues to: [project maintainers]

---

## ❓ Questions?

- 💬 [GitHub Discussions](https://github.com/Cnd-North/adsb-flight-tracker/discussions)
- 🐛 [Issues](https://github.com/Cnd-North/adsb-flight-tracker/issues)
- 📧 Email: your-email@example.com

---

## 🎉 Recognition

Contributors are listed in:
- [Contributors page](https://github.com/Cnd-North/adsb-flight-tracker/graphs/contributors)
- Release notes
- README acknowledgments

Thank you for helping make ADS-B tracking better for everyone! ✈️

---

**Happy Contributing!** 🚀
