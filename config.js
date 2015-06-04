module.exports = function (config) {

  // Output directory
  config.dest = 'target/www';

  // Images minification
  config.minify_images = true;

  // Javascript minification
  config.minify_js = false;
  config.generate_js_maps = false;

  // Development web server
  config.server = false;
};
