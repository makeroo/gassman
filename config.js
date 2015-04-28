module.exports = function (config) {

  // Output directory
  config.dest = 'target/www';

  // Images minification
  config.minify_images = true;

  // Development web server

  config.server = false;

  // Set to false to disable it:
  // config.server = false;
};
