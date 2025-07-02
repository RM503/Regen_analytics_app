// This script contains utility functions to be used by the main app.

// Function to remove cloud and snow pixels
var utils = {
    maskCloudAndShadows: function(image) {
      /*
      This function masks clouds and shadows using Sentinel-2
      'Scene Classification Layer' (SCL). By default, the cloud
      probability is set to 15%. Smaller values can lead to loss
      of data points.
      */
      var cloudProb = image.select('MSK_CLDPRB');
      var snowProb = image.select('MSK_SNWPRB');
      var cloud = cloudProb.lt(15);
      var snow = snowProb.lt(15);
      var scl = image.select('SCL'); 
      var shadow = scl.eq(3);
      var cirrus = scl.eq(10); 
      var mask = (cloud.and(snow)).and(cirrus.neq(1)).and(shadow.neq(1));
      
      return image.updateMask(mask);
    },
    addNDVI: function(image) {
      var ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi');
      return image.addBands([ndvi]);
    },
    addNDMI: function(image) {
      var ndmi = image.normalizedDifference(['B8', 'B11']).rename('ndmi');
      return image.addBands([ndmi]);
    }
  };
  
  exports = utils;