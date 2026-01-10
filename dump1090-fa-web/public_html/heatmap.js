/**
 * Signal Strength Heatmap Overlay
 * Displays altitude-sliced heatmaps showing signal strength distribution
 */

class SignalHeatmap {
    constructor() {
        this.heatmapData = null;
        this.currentAltitudeIndex = 2; // Default to 5,000-10,000 ft
        this.heatmapLayer = null;
        this.heatmapLayers = []; // Array to hold all altitude layers
        this.enabled = false;
        this.showAll = false; // Toggle for showing all altitudes
        this.updateInterval = 30000; // Update every 30 seconds
    }

    async init() {
        // Wait for the map to be initialized
        await this.waitForMap();

        // Load initial data
        await this.loadHeatmapData();

        // Create the heatmap layer (initially hidden)
        this.createHeatmapLayer();

        // Auto-update data
        setInterval(() => {
            if (this.enabled) {
                this.loadHeatmapData();
            }
        }, this.updateInterval);

        console.log('Signal Heatmap initialized');
    }

    waitForMap() {
        return new Promise((resolve) => {
            const checkMap = setInterval(() => {
                if (typeof OLMap !== 'undefined' && OLMap) {
                    clearInterval(checkMap);
                    resolve();
                }
            }, 100);
        });
    }

    async loadHeatmapData() {
        try {
            const response = await fetch('http://'+window.location.hostname+':8081/api/heatmap');
            this.heatmapData = await response.json();
            console.log('Heatmap data loaded:', this.heatmapData.total_points, 'points');

            // Update the layer if it's enabled
            if (this.enabled && this.heatmapLayer) {
                this.updateHeatmapLayer();
            }
        } catch (error) {
            console.error('Failed to load heatmap data:', error);
        }
    }

    createHeatmapLayer() {
        // Create a vector source for the heatmap
        const vectorSource = new ol.source.Vector();

        // Create the heatmap layer
        this.heatmapLayer = new ol.layer.Heatmap({
            source: vectorSource,
            blur: 25,
            radius: 15,
            weight: function(feature) {
                return feature.get('weight');
            },
            gradient: [
                '#00000000',  // Transparent at 0%
                '#ef4444',    // Red at weak signal
                '#f59e0b',    // Orange
                '#fbbf24',    // Yellow
                '#84cc16',    // Yellow-green
                '#4ade80'     // Green at strong signal
            ],
            opacity: 0.6,
            visible: false // Start hidden
        });

        // Add to map
        OLMap.addLayer(this.heatmapLayer);
    }

    createAllHeatmapLayers() {
        // Create 5 layers, one for each altitude range
        // Clear existing layers if any
        this.heatmapLayers.forEach(layer => OLMap.removeLayer(layer));
        this.heatmapLayers = [];

        for (let i = 0; i < 5; i++) {
            const vectorSource = new ol.source.Vector();
            const layer = new ol.layer.Heatmap({
                source: vectorSource,
                blur: 20,
                radius: 12,
                weight: function(feature) {
                    return feature.get('weight');
                },
                gradient: [
                    '#00000000',
                    '#ef4444',
                    '#f59e0b',
                    '#fbbf24',
                    '#84cc16',
                    '#4ade80'
                ],
                opacity: 0.4, // Lower opacity for overlapping layers
                visible: false
            });
            OLMap.addLayer(layer);
            this.heatmapLayers.push(layer);
        }
    }

    updateHeatmapLayer() {
        if (!this.heatmapData || !this.heatmapLayer) return;

        const source = this.heatmapLayer.getSource();
        source.clear();

        // Get the current altitude range data
        const rangeData = this.heatmapData.altitude_ranges[this.currentAltitudeIndex];

        if (!rangeData || !rangeData.points) {
            console.log('No data for altitude range:', this.currentAltitudeIndex);
            return;
        }

        console.log('Displaying', rangeData.points.length, 'points for', rangeData.label);

        // Add features to the source
        rangeData.points.forEach(point => {
            const feature = new ol.Feature({
                geometry: new ol.geom.Point(
                    ol.proj.fromLonLat([point.lon, point.lat])
                ),
                weight: point.weight
            });
            source.addFeature(feature);
        });
    }

    updateAllHeatmapLayers() {
        if (!this.heatmapData || this.heatmapLayers.length === 0) {
            // Create layers if they don't exist
            this.createAllHeatmapLayers();
        }

        if (!this.heatmapData) return;

        // Update each altitude layer
        this.heatmapData.altitude_ranges.forEach((rangeData, index) => {
            if (index >= this.heatmapLayers.length) return;

            const source = this.heatmapLayers[index].getSource();
            source.clear();

            if (!rangeData.points) return;

            console.log(`Updating layer ${index}: ${rangeData.label} with ${rangeData.points.length} points`);

            rangeData.points.forEach(point => {
                const feature = new ol.Feature({
                    geometry: new ol.geom.Point(
                        ol.proj.fromLonLat([point.lon, point.lat])
                    ),
                    weight: point.weight
                });
                source.addFeature(feature);
            });
        });
    }

    toggle(enabled) {
        this.enabled = enabled;

        if (this.showAll) {
            // Toggle all layers
            this.heatmapLayers.forEach(layer => layer.setVisible(enabled));
            if (enabled && this.heatmapLayers.length === 0) {
                this.updateAllHeatmapLayers();
            }
        } else {
            // Toggle single layer
            if (this.heatmapLayer) {
                this.heatmapLayer.setVisible(enabled);
                if (enabled) {
                    this.updateHeatmapLayer();
                }
            }
        }
        console.log('Heatmap', enabled ? 'enabled' : 'disabled');
    }

    toggleShowAll(showAll) {
        this.showAll = showAll;

        if (showAll) {
            // Hide single layer
            if (this.heatmapLayer) {
                this.heatmapLayer.setVisible(false);
            }
            // Show all layers
            if (this.enabled) {
                this.updateAllHeatmapLayers();
                this.heatmapLayers.forEach(layer => layer.setVisible(true));
            }
        } else {
            // Hide all layers
            this.heatmapLayers.forEach(layer => layer.setVisible(false));
            // Show single layer
            if (this.enabled && this.heatmapLayer) {
                this.heatmapLayer.setVisible(true);
                this.updateHeatmapLayer();
            }
        }
        console.log('Show all altitudes:', showAll);
    }

    setAltitudeRange(index) {
        this.currentAltitudeIndex = index;
        if (this.enabled) {
            this.updateHeatmapLayer();
        }

        // Update the label
        if (this.heatmapData && this.heatmapData.altitude_ranges[index]) {
            const label = this.heatmapData.altitude_ranges[index].label;
            const labelElement = document.getElementById('heatmap-altitude-label');
            if (labelElement) {
                labelElement.textContent = label;
            }
        }
    }

    getAltitudeRanges() {
        if (!this.heatmapData) return [];
        return this.heatmapData.altitude_ranges.map((range, index) => ({
            index: index,
            label: range.label,
            count: range.point_count
        }));
    }
}

// Initialize when DOM is ready
let signalHeatmap;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        signalHeatmap = new SignalHeatmap();
        signalHeatmap.init();
    });
} else {
    signalHeatmap = new SignalHeatmap();
    signalHeatmap.init();
}
