/********************  CONFIG  ********************/
var START_DATE = '2020-01-01';
var END_DATE   = '2025-05-31';
var MAX_POLYGONS = 10;

/********************  UI & MAP  ********************/
var map = ui.Map();
map.setCenter(38, 1, 7);
map.setOptions('HYBRID');

var drawingTools = map.drawingTools();
drawingTools.setShown(true);
drawingTools.setDrawModes(['rectangle', 'polygon']);
drawingTools.draw();

/********************  PANELS  ********************/
var infoPanel = ui.Panel({
  widgets: [
    ui.Label('Sentinel‑2 VI time‑series generator', {fontSize: '20px', fontWeight: 'bold'}),
    ui.Label('Draw polygon(s) to generate time‑series data')
  ],
  style: {stretch: 'horizontal'}
});

var chartPanel = ui.Panel({layout: ui.Panel.Layout.flow('vertical')});

var sidebar = ui.Panel({
  widgets: [
    infoPanel,
    chartPanel,
    ui.Button({
      label: 'Show Accepted Polygons',
      onClick: showAcceptedPolygons
    }),
    ui.Button({
      label: 'Reset Geometries',
      onClick: resetAll
    })
  ],
  style: {width: '30%', padding: '10px'}
});

ui.root.widgets().reset([sidebar, map]);

/********************  DATA & UTILS  ********************/
var utils = require('users/rmahbub503/DataKind_Geospatial:web_app/utils.js');

// Load once; we’ll clip/filter later when the user draws.
var baseCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterDate(START_DATE, END_DATE)
  .map(utils.maskCloudAndShadows)
  .map(utils.addNDVI)
  .map(utils.addNDMI);

/********************  STATE  ********************/
var acceptedPolygons = [];   // client‑side list

/********************  DRAW CALLBACK  ********************/
function onDrawComplete() {
  if (acceptedPolygons.length >= MAX_POLYGONS) {
    print('⚠️  Max number of polygons (' + MAX_POLYGONS + ') reached.');
    drawingTools.layers().clear();
    return;
  }

  var geom = drawingTools.layers().get(0).getEeObject();
  //drawingTools.layers().clear();  // immediately clear drawing layer

  // Check area (≤ 100 km²)
  geom.area(1).divide(1e6).evaluate(function(km2) {
    if (km2 > 100) {
      print('❌ Area too large (' + km2.toFixed(2) + ' km²). Draw a smaller polygon.');
      return;
    }

    // Accept the polygon
    acceptedPolygons.push(geom);
    print('✅ Polygon accepted (' + km2.toFixed(2) + ' km²). Total: ' + acceptedPolygons.length);

    // Update chart & map overlay
    updateChart();
    addPolygonLayer(geom, acceptedPolygons.length);
  });
}
drawingTools.onDraw(onDrawComplete);

/********************  CHART GENERATION  ********************/
function updateChart() {
  if (acceptedPolygons.length === 0) {
    chartPanel.clear();
    return;
  }

  // Build a fresh FeatureCollection with labels
  var fc = ee.FeatureCollection(
    acceptedPolygons.map(function(g, i) {
      return ee.Feature(g, {'poly_id': 'Polygon ' + (i + 1)});
    })
  );

  // Filter the big collection to the combined geometry to speed things up
  var filteredCol = baseCollection.filterBounds(fc.geometry());

  var chart1 = ui.Chart.image.seriesByRegion({
      imageCollection: filteredCol.select('ndvi'),
      regions: fc,
      reducer: ee.Reducer.mean(),
      seriesProperty: 'poly_id',
      scale: 10,
      xProperty: 'system:time_start'
    })
    .setChartType('LineChart')
    .setOptions({
      title: 'NDVI time‑series',
      lineWidth: 2,
      interpolateNulls: true,
      hAxis: {title: 'Date'},
      vAxis: {title: 'Index value'},
      legend: {position: 'right'}
    });
    
  var chart2 = ui.Chart.image.seriesByRegion({
      imageCollection: filteredCol.select('ndmi'),
      regions: fc,
      reducer: ee.Reducer.mean(),
      seriesProperty: 'poly_id',
      scale: 10,
      xProperty: 'system:time_start'
    })
    .setChartType('LineChart')
    .setOptions({
      title: 'NDMI time‑series',
      lineWidth: 2,
      interpolateNulls: true,
      hAxis: {title: 'Date'},
      vAxis: {title: 'Index value'},
      legend: {position: 'right'}
    });

  chartPanel.clear();
  chartPanel.add(chart1);
  chartPanel.add(chart2);
}

/********************  MAP HELPERS  ********************/
function addPolygonLayer(geom, idx) {
  var layerStyle = {color: 'blue', strokeWidth: 2};
  map.addLayer(geom, layerStyle, 'Polygon ' + idx, false);
}

function showAcceptedPolygons() {
  if (acceptedPolygons.length === 0) {
    print('⚠️  No polygons to show.');
    return;
  }
  var fc = ee.FeatureCollection(acceptedPolygons.map(function(g){return ee.Feature(g);}));
  map.addLayer(fc, {color: 'blue'}, 'Accepted Polygons');
}

/********************  RESET  ********************/
function resetAll() {
  acceptedPolygons = [];
  chartPanel.clear();
  map.layers().reset();
  map.setCenter(38, 1, 7);
  drawingTools.layers().reset();
  print('🔄  All cleared.');
}
