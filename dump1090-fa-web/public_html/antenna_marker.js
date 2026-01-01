/**
 * Antenna Marker - Shows antenna location on the map
 * Fetches antenna location from coverage API and displays it
 */

(async function() {
    // Wait for the map to be initialized
    function waitForMap() {
        return new Promise((resolve) => {
            const checkMap = setInterval(() => {
                if (typeof OLMap !== 'undefined' && OLMap) {
                    clearInterval(checkMap);
                    resolve();
                }
            }, 100);
        });
    }

    await waitForMap();

    try {
        // Fetch antenna location
        const response = await fetch('http://localhost:8081/api/coverage');
        const data = await response.json();

        if (!data.antenna) return;

        const antenna = data.antenna;

        // Create antenna marker
        const antennaFeature = new ol.Feature({
            geometry: new ol.geom.Point(
                ol.proj.fromLonLat([antenna.longitude, antenna.latitude])
            ),
            name: 'Your Antenna',
            type: 'antenna'
        });

        // Style for antenna marker
        const antennaStyle = new ol.style.Style({
            image: new ol.style.Circle({
                radius: 8,
                fill: new ol.style.Fill({
                    color: 'rgba(255, 0, 0, 0.8)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#fff',
                    width: 3
                })
            }),
            text: new ol.style.Text({
                text: '📡',
                font: '20px sans-serif',
                offsetY: -20
            })
        });

        antennaFeature.setStyle(antennaStyle);

        // Create vector source and layer
        const antennaSource = new ol.source.Vector({
            features: [antennaFeature]
        });

        const antennaLayer = new ol.layer.Vector({
            source: antennaSource,
            zIndex: 1000
        });

        // Add to map
        OLMap.addLayer(antennaLayer);

        // Add range rings (optional)
        const rangeRings = [10, 20, 50, 100]; // km
        rangeRings.forEach(range => {
            const circle = new ol.geom.Circle(
                ol.proj.fromLonLat([antenna.longitude, antenna.latitude]),
                range * 1000 // km to meters
            );

            const circleFeature = new ol.Feature({
                geometry: circle
            });

            const circleStyle = new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'rgba(255, 255, 255, 0.3)',
                    width: 1,
                    lineDash: [5, 5]
                })
            });

            circleFeature.setStyle(circleStyle);
            antennaSource.addFeature(circleFeature);
        });

        // Add popup on click
        OLMap.on('click', function(evt) {
            const feature = OLMap.forEachFeatureAtPixel(evt.pixel, function(feature) {
                return feature;
            });

            if (feature && feature.get('type') === 'antenna') {
                alert(`Antenna Location\n` +
                      `Latitude: ${antenna.latitude.toFixed(6)}°\n` +
                      `Longitude: ${antenna.longitude.toFixed(6)}°\n` +
                      `Est. Height: ${antenna.height_feet.toFixed(0)} ft\n` +
                      `Confidence: ${antenna.confidence}\n` +
                      `Samples: ${antenna.samples}`);
            }
        });

        console.log('Antenna marker added to map');

    } catch (error) {
        console.error('Failed to add antenna marker:', error);
    }
})();
