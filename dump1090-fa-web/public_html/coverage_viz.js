/**
 * Coverage Visualization Library
 * Creates polar charts and coverage maps for antenna analysis
 */

class CoverageViz {
    constructor() {
        this.coverageData = null;
        this.charts = {};
        this.updateInterval = 10000; // Update every 10 seconds
    }

    async init() {
        await this.loadCoverageData();
        this.createCoverageCharts();
        this.displayAntennaInfo();

        // Auto-update
        setInterval(() => {
            this.loadCoverageData();
            this.updateCharts();
        }, this.updateInterval);
    }

    async loadCoverageData() {
        try {
            const response = await fetch('http://localhost:8081/api/coverage');
            this.coverageData = await response.json();
            return this.coverageData;
        } catch (error) {
            console.error('Failed to load coverage data:', error);
            return null;
        }
    }

    createCoverageCharts() {
        if (!this.coverageData) return;

        this.createPolarChart();
        this.createDirectionTable();
    }

    createPolarChart() {
        const canvas = document.getElementById('coverage-polar-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const directions = this.coverageData.coverage_by_direction;

        // Extract data for chart
        const labels = directions.map(d => d.direction);
        const distances = directions.map(d => d.max_distance);
        const rssi_values = directions.map(d => d.avg_rssi);
        const counts = directions.map(d => d.count);

        // Calculate max distance and set scale to show max 10-11 rings with nice round step sizes
        const maxDistance = Math.max(...distances);

        // Divide max by 10, round to nearest 10 to get step size
        const stepSize = Math.ceil(maxDistance / 10 / 10) * 10;
        const chartMax = stepSize * 10; // 10 rings

        console.log('Coverage Chart - Max Distance:', maxDistance, 'km');
        console.log('Step Size:', stepSize, 'km, Chart Max:', chartMax, 'km');
        console.log('Number of rings:', chartMax / stepSize);
        console.log('All labels:', labels);

        // Helper function to check if a label is cardinal/ordinal
        const isCardinal = (label) => {
            const result = ['N', 'E', 'S', 'W'].includes(label);
            if (result) console.log('Cardinal direction found:', label);
            return result;
        };
        const isOrdinal = (label) => {
            const result = ['NE', 'SE', 'SW', 'NW'].includes(label);
            if (result) console.log('Ordinal direction found:', label);
            return result;
        };

        // Function to get color based on RSSI (signal strength)
        // RSSI is in dBFS (negative values, closer to 0 is stronger)
        const getColorFromRSSI = (rssi, alpha = 0.6) => {
            if (rssi === null || rssi === undefined) {
                return `rgba(100, 100, 100, ${alpha})`; // Gray for no data
            }
            // Excellent: > -15 dBFS (green)
            if (rssi > -15) return `rgba(74, 222, 128, ${alpha})`;
            // Good: -15 to -20 dBFS (yellow-green)
            if (rssi > -20) return `rgba(251, 191, 36, ${alpha})`;
            // Fair: -20 to -25 dBFS (orange)
            if (rssi > -25) return `rgba(255, 159, 64, ${alpha})`;
            // Poor: < -25 dBFS (red)
            return `rgba(239, 68, 68, ${alpha})`;
        };

        // Destroy existing chart
        if (this.charts.polar) {
            this.charts.polar.destroy();
        }

        this.charts.polar = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Max Range (km)',
                    data: distances,
                    backgroundColor: rssi_values.map(rssi => getColorFromRSSI(rssi, 0.6)),
                    borderColor: rssi_values.map(rssi => getColorFromRSSI(rssi, 1)),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                layout: {
                    padding: {
                        top: 40,
                        right: 40,
                        bottom: 40,
                        left: 40
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            generateLabels: function() {
                                return [
                                    {
                                        text: 'Excellent Signal (> -15 dBFS)',
                                        fillStyle: 'rgba(74, 222, 128, 0.6)',
                                        strokeStyle: 'rgba(74, 222, 128, 1)',
                                        lineWidth: 2
                                    },
                                    {
                                        text: 'Good Signal (-15 to -20 dBFS)',
                                        fillStyle: 'rgba(251, 191, 36, 0.6)',
                                        strokeStyle: 'rgba(251, 191, 36, 1)',
                                        lineWidth: 2
                                    },
                                    {
                                        text: 'Fair Signal (-20 to -25 dBFS)',
                                        fillStyle: 'rgba(255, 159, 64, 0.6)',
                                        strokeStyle: 'rgba(255, 159, 64, 1)',
                                        lineWidth: 2
                                    },
                                    {
                                        text: 'Poor Signal (< -25 dBFS)',
                                        fillStyle: 'rgba(239, 68, 68, 0.6)',
                                        strokeStyle: 'rgba(239, 68, 68, 1)',
                                        lineWidth: 2
                                    },
                                    {
                                        text: 'No Coverage',
                                        fillStyle: 'rgba(100, 100, 100, 0.3)',
                                        strokeStyle: 'rgba(100, 100, 100, 0.5)',
                                        lineWidth: 2
                                    }
                                ];
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Antenna Coverage Pattern',
                        color: '#fff',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const dir = directions[index];
                                return [
                                    `Direction: ${dir.direction}`,
                                    `Max Range: ${dir.max_distance} km`,
                                    `Detections: ${dir.count}`,
                                    dir.avg_rssi ? `Avg RSSI: ${dir.avg_rssi} dBFS` : ''
                                ].filter(Boolean);
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: chartMax,
                        angleLines: {
                            color: function(context) {
                                // Make cardinal directions (N, E, S, W) solid and brighter
                                const label = labels[context.index];
                                return isCardinal(label) ? 'rgba(74, 222, 128, 0.6)' : 'rgba(255, 255, 255, 0.2)';
                            },
                            lineWidth: function(context) {
                                const label = labels[context.index];
                                return isCardinal(label) ? 3 : 1;
                            }
                        },
                        ticks: {
                            color: '#fff',
                            backdropColor: 'rgba(0, 0, 0, 0.7)',
                            backdropPadding: 4,
                            font: {
                                size: 11,
                                weight: 'bold'
                            },
                            callback: function(value) {
                                return value + ' km';
                            },
                            stepSize: stepSize
                        },
                        grid: {
                            color: function(context) {
                                // Alternate colors for concentric rings for easier reading
                                const value = context.tick.value;
                                if (value === 0) return 'rgba(255, 255, 255, 0.3)';
                                // Every other ring - brighter green
                                if (value % (stepSize * 2) === 0) return 'rgba(74, 222, 128, 0.4)';
                                // Regular rings - medium white
                                return 'rgba(255, 255, 255, 0.2)';
                            },
                            lineWidth: function(context) {
                                const value = context.tick.value;
                                // Make every other ring thicker
                                if (value % (stepSize * 2) === 0) return 2;
                                return 1;
                            },
                            circular: true
                        },
                        pointLabels: {
                            display: true,
                            centerPointLabels: false,
                            color: function(context) {
                                const label = labels[context.index];
                                // Cardinal directions (N, E, S, W) - bright green
                                if (isCardinal(label)) {
                                    return '#4ade80';
                                }
                                // Ordinal directions (NE, SE, SW, NW) - yellow
                                if (isOrdinal(label)) {
                                    return '#fbbf24';
                                }
                                // All other directions - white
                                return '#fff';
                            },
                            font: function(context) {
                                const label = labels[context.index];

                                return {
                                    size: isCardinal(label) ? 18 : isOrdinal(label) ? 15 : 12,
                                    weight: isCardinal(label) ? 'bold' : isOrdinal(label) ? 'bold' : 'normal',
                                    family: 'Arial, sans-serif'
                                };
                            },
                            backdropColor: function(context) {
                                const label = labels[context.index];

                                if (isCardinal(label)) return 'rgba(40, 40, 40, 0.9)'; // Dark grey for cardinals
                                if (isOrdinal(label)) return 'rgba(60, 60, 60, 0.85)'; // Medium grey for ordinals
                                return 'rgba(0, 0, 0, 0.7)'; // Black for others
                            },
                            backdropPadding: function(context) {
                                const label = labels[context.index];

                                return isCardinal(label) ? 6 : isOrdinal(label) ? 5 : 3;
                            },
                            borderRadius: 4,
                            padding: 4
                        }
                    }
                }
            }
        });
    }

    createDirectionTable() {
        const tableBody = document.getElementById('coverage-table-body');
        if (!tableBody || !this.coverageData) return;

        const directions = this.coverageData.coverage_by_direction;

        // Clear existing rows
        tableBody.innerHTML = '';

        // Function to get signal indicator based on RSSI
        const getSignalIndicator = (rssi) => {
            if (!rssi) return '⚫';
            if (rssi > -15) return '🟢'; // Excellent
            if (rssi > -20) return '🟡'; // Good
            if (rssi > -25) return '🟠'; // Fair
            return '🔴'; // Poor
        };

        // Add rows for directions with coverage
        directions.filter(d => d.count > 0).forEach(dir => {
            const row = document.createElement('tr');
            const signal = getSignalIndicator(dir.avg_rssi);

            row.innerHTML = `
                <td style="text-align: center;">${signal} ${dir.direction}</td>
                <td style="text-align: center;">${dir.count}</td>
                <td style="text-align: center;">${dir.max_distance} km</td>
                <td style="text-align: center;">${dir.avg_rssi ? dir.avg_rssi.toFixed(1) : 'N/A'} dBFS</td>
            `;
            tableBody.appendChild(row);
        });

        // Show blind spots
        const blindSpots = directions.filter(d => d.count === 0);
        if (blindSpots.length > 0) {
            const row = document.createElement('tr');
            row.style.opacity = '0.5';
            row.innerHTML = `
                <td colspan="4" style="text-align: center; font-style: italic;">
                    No coverage: ${blindSpots.map(d => d.direction).join(', ')}
                </td>
            `;
            tableBody.appendChild(row);
        }
    }

    displayAntennaInfo() {
        if (!this.coverageData) return;

        const antenna = this.coverageData.antenna;

        // Update antenna location display
        const elements = {
            'antenna-lat': antenna.latitude.toFixed(6),
            'antenna-lon': antenna.longitude.toFixed(6),
            'antenna-height-m': antenna.height_meters.toFixed(1),
            'antenna-height-ft': antenna.height_feet.toFixed(0),
            'antenna-confidence': antenna.confidence.toUpperCase(),
            'antenna-samples': antenna.samples.toLocaleString()
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update confidence color
        const confidenceEl = document.getElementById('antenna-confidence');
        if (confidenceEl) {
            confidenceEl.className = `confidence-badge confidence-${antenna.confidence}`;
        }
    }

    updateCharts() {
        if (!this.coverageData) return;

        this.createPolarChart();
        this.createDirectionTable();
        this.displayAntennaInfo();
    }
}

// Initialize when DOM is ready
let coverageViz;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        coverageViz = new CoverageViz();
        coverageViz.init();
    });
} else {
    coverageViz = new CoverageViz();
    coverageViz.init();
}
