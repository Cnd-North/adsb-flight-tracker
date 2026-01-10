/**
 * Homepage Status Bar Integration
 * Updates the existing status bar with live service information
 * Only for index.html - other pages use floating panel
 */

class HomepageStatus {
    constructor() {
        this.updateInterval = 5000; // Update every 5 seconds
        this.init();
    }

    async init() {
        await this.update();
        setInterval(() => this.update(), this.updateInterval);
    }

    async update() {
        try {
            const response = await fetch('http://'+window.location.hostname+':8081/api/status');
            const data = await response.json();
            this.updateStatusBar(data);
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }

    updateStatusBar(data) {
        const services = data.services;

        // Count running services
        const total = Object.keys(services).length;
        const running = Object.values(services).filter(v => v).length;

        // Update main status indicator
        const indicator = document.getElementById('status_indicator');
        const statusText = document.getElementById('status_text');

        if (indicator && statusText) {
            if (running === total) {
                indicator.style.background = '#4ade80'; // Green
                indicator.style.boxShadow = '0 0 8px #4ade80';
                statusText.textContent = `All Systems Operational (${running}/${total})`;
                statusText.style.color = '#4ade80';
            } else if (running > 0) {
                indicator.style.background = '#fbbf24'; // Yellow
                indicator.style.boxShadow = '0 0 8px #fbbf24';
                statusText.textContent = `${running}/${total} Services Running`;
                statusText.style.color = '#fbbf24';
            } else {
                indicator.style.background = '#ef4444'; // Red
                indicator.style.boxShadow = '0 0 8px #ef4444';
                statusText.textContent = 'System Offline';
                statusText.style.color = '#ef4444';
            }

            // Add dropdown toggle if not already added
            if (!document.getElementById('status-dropdown-toggle')) {
                const toggleArrow = document.createElement('span');
                toggleArrow.id = 'status-dropdown-toggle';
                toggleArrow.innerHTML = '▼';
                toggleArrow.style.cssText = 'cursor: pointer; margin-left: 8px; font-size: 10px; transition: transform 0.2s;';
                toggleArrow.onclick = () => this.toggleDropdown();
                statusText.appendChild(toggleArrow);

                statusText.style.cursor = 'pointer';
                statusText.onclick = (e) => {
                    if (e.target !== toggleArrow) this.toggleDropdown();
                };
            }
        }

        // Create or update services dropdown
        this.updateServicesDropdown(services, data.database);

        // Update database stats in the bar
        const statsDiv = document.getElementById('system_status');
        if (statsDiv && !document.getElementById('db-stats')) {
            // Add database stats next to the status indicator
            const dbStatsDiv = document.createElement('div');
            dbStatsDiv.id = 'db-stats';
            dbStatsDiv.style.cssText = 'display: flex; gap: 15px; margin-left: 15px; padding-left: 15px; border-left: 1px solid #555;';
            dbStatsDiv.innerHTML = `
                <div style="font-size: 11px; opacity: 0.8;">
                    Today: <span id="flights-today" style="font-weight: bold; color: #4ade80;">--</span>
                </div>
                <div style="font-size: 11px; opacity: 0.8;">
                    Total: <span id="flights-total" style="font-weight: bold; color: #4ade80;">--</span>
                </div>
                <div style="font-size: 11px; opacity: 0.8;">
                    Positions: <span id="positions-logged" style="font-weight: bold; color: #4ade80;">--</span>
                </div>
            `;

            const firstDiv = statsDiv.querySelector('div');
            if (firstDiv) {
                firstDiv.appendChild(dbStatsDiv);
            }
        }

        // Update database stats values
        const flightsToday = document.getElementById('flights-today');
        const flightsTotal = document.getElementById('flights-total');
        const positionsLogged = document.getElementById('positions-logged');

        if (flightsToday) flightsToday.textContent = data.database.flights_today.toLocaleString();
        if (flightsTotal) flightsTotal.textContent = data.database.total_flights.toLocaleString();
        if (positionsLogged) positionsLogged.textContent = data.database.positions_logged.toLocaleString();
    }

    updateServicesDropdown(services, database) {
        let dropdown = document.getElementById('status-services-dropdown');

        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'status-services-dropdown';
            dropdown.style.cssText = `
                display: none;
                position: absolute;
                top: 100%;
                left: 0;
                background: rgba(0, 0, 0, 0.95);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 15px;
                margin-top: 5px;
                min-width: 300px;
                z-index: 100000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            `;

            const statusDiv = document.getElementById('system_status');
            if (statusDiv) {
                statusDiv.style.position = 'relative';
                statusDiv.appendChild(dropdown);
            }
        }

        // Build services list
        const servicesHTML = Object.entries(services).map(([key, running]) => {
            const icon = running ? '🟢' : '🔴';
            const name = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const color = running ? '#4ade80' : '#ef4444';
            return `
                <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333;">
                    <span>${icon} ${name}</span>
                    <span style="color: ${color}; font-weight: bold;">${running ? 'Running' : 'Stopped'}</span>
                </div>
            `;
        }).join('');

        dropdown.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px; color: #4ade80;">Service Status</div>
            ${servicesHTML}
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #555;">
                <div style="font-weight: bold; margin-bottom: 5px; color: #4ade80;">Database Stats</div>
                <div style="font-size: 12px; opacity: 0.9;">
                    Flights Today: <strong>${database.flights_today.toLocaleString()}</strong><br>
                    Total Flights: <strong>${database.total_flights.toLocaleString()}</strong><br>
                    Positions: <strong>${database.positions_logged.toLocaleString()}</strong>
                </div>
            </div>
        `;
    }

    toggleDropdown() {
        const dropdown = document.getElementById('status-services-dropdown');
        const toggle = document.getElementById('status-dropdown-toggle');

        if (dropdown && toggle) {
            const isHidden = dropdown.style.display === 'none';
            dropdown.style.display = isHidden ? 'block' : 'none';
            toggle.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new HomepageStatus();
    });
} else {
    new HomepageStatus();
}
