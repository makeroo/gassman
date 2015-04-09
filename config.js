module.exports = function (config) {

  // Output directory
  config.dest = 'target/www';

  // Images minification
  config.minify_images = true;

  // Development web server

  config.server = true;

  // Set to false to disable it:
  // config.server = false;
  
  // 3rd party components
  // config.vendor.js.push('.bower_components/lib/dist/lib.js');

  // config.vendor.fonts.push('.bower_components/font/dist/*');
};