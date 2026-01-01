/**
 * Signal Strength Heatmap Overlay
 * Displays altitude-sliced heatmaps showing signal strength distribution
 */

class SignalHeatmap {
    constructor() {
        this.heatmapData = null;
        this.currentAltitudeIndex = 2; // Default to 5,000-10,000 ft
        this.heatmapLayer = null;
        this.enabled = false;
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
            const response = await fetch('http://localhost:8081/api/heatmap');
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

    toggle(enabled) {
        this.enabled = enabled;
        if (this.heatmapLayer) {
            this.heatmapLayer.setVisible(enabled);
            if (enabled) {
                this.updateHeatmapLayer();
            }
        }
        console.log('Heatmap', enabled ? 'enabled' : 'disabled');
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
