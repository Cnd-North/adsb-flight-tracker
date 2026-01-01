/**
 * Status Indicator - Shows which backend services are running
 * Displays a live status panel on all web pages
 */

class StatusIndicator {
    constructor() {
        this.statusElement = null;
        this.updateInterval = 5000; // Update every 5 seconds
        this.init();
    }

    init() {
        // Create status panel HTML
        const panel = document.createElement('div');
        panel.id = 'system-status-panel';
        panel.innerHTML = `
            <div class="status-header">
                <span class="status-title">System Status</span>
                <span class="status-toggle collapsed" onclick="statusIndicator.toggle()">▼</span>
            </div>
            <div class="status-body collapsed" id="status-body">
                <div class="status-loading">Loading...</div>
            </div>
        `;
        document.body.appendChild(panel);

        this.statusElement = document.getElementById('status-body');

        // Add CSS
        this.injectStyles();

        // Start updating
        this.update();
        setInterval(() => this.update(), this.updateInterval);
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #system-status-panel {
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.85);
                color: #fff;
                padding: 10px;
                border-radius: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 13px;
                z-index: 99999;
                min-width: 250px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                backdrop-filter: blur(10px);
            }

            .status-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.2);
                cursor: pointer;
            }

            .status-title {
                font-weight: 600;
                font-size: 14px;
            }

            .status-toggle {
                cursor: pointer;
                user-select: none;
                transition: transform 0.2s;
            }

            .status-toggle.collapsed {
                transform: rotate(-90deg);
            }

            .status-body {
                max-height: 400px;
                overflow-y: auto;
                transition: max-height 0.3s ease;
            }

            .status-body.collapsed {
                max-height: 0;
                overflow: hidden;
            }

            .status-service {
                display: flex;
                align-items: center;
                padding: 6px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }

            .status-service:last-child {
                border-bottom: none;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 10px;
                flex-shrink: 0;
            }

            .status-indicator.running {
                background: #4ade80;
                box-shadow: 0 0 8px #4ade80;
            }

            .status-indicator.stopped {
                background: #ef4444;
                box-shadow: 0 0 8px #ef4444;
            }

            .status-name {
                flex: 1;
                font-size: 12px;
            }

            .status-stats {
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(255,255,255,0.2);
                font-size: 11px;
            }

            .status-stat {
                display: flex;
                justify-content: space-between;
                padding: 3px 0;
                opacity: 0.8;
            }

            .status-stat-label {
                color: rgba(255,255,255,0.7);
            }

            .status-stat-value {
                font-weight: 600;
                color: #4ade80;
            }

            .status-loading {
                text-align: center;
                opacity: 0.5;
                padding: 10px;
            }

            .status-error {
                color: #ef4444;
                padding: 10px;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    }

    async update() {
        try {
            const response = await fetch('http://localhost:8081/api/status');
            const data = await response.json();
            this.render(data);
        } catch (error) {
            this.renderError();
        }
    }

    render(data) {
        const services = [
            { key: 'dump1090', name: 'dump1090 (SDR Decoder)' },
            { key: 'flight_logger', name: 'Flight Logger' },
            { key: 'log_server', name: 'Log API Server' },
            { key: 'position_tracker', name: 'Position Tracker' },
            { key: 'signal_logger', name: 'Signal Logger' },
            { key: 'web_server', name: 'Web Server' }
        ];

        let html = '';

        services.forEach(service => {
            const isRunning = data.services[service.key];
            const statusClass = isRunning ? 'running' : 'stopped';
            html += `
                <div class="status-service">
                    <div class="status-indicator ${statusClass}"></div>
                    <div class="status-name">${service.name}</div>
                </div>
            `;
        });

        // Add database stats
        html += `
            <div class="status-stats">
                <div class="status-stat">
                    <span class="status-stat-label">Total Flights:</span>
                    <span class="status-stat-value">${data.database.total_flights.toLocaleString()}</span>
                </div>
                <div class="status-stat">
                    <span class="status-stat-label">Today's Flights:</span>
                    <span class="status-stat-value">${data.database.flights_today.toLocaleString()}</span>
                </div>
                <div class="status-stat">
                    <span class="status-stat-label">Positions Logged:</span>
                    <span class="status-stat-value">${data.database.positions_logged.toLocaleString()}</span>
                </div>
            </div>
        `;

        this.statusElement.innerHTML = html;
    }

    renderError() {
        this.statusElement.innerHTML = '<div class="status-error">Unable to connect to API server</div>';
    }

    toggle() {
        const body = document.getElementById('status-body');
        const toggle = document.querySelector('.status-toggle');

        body.classList.toggle('collapsed');
        toggle.classList.toggle('collapsed');
    }
}

// Initialize when DOM is ready
let statusIndicator;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        statusIndicator = new StatusIndicator();
    });
} else {
    statusIndicator = new StatusIndicator();
}
