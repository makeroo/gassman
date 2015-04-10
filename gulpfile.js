/*=====================================
=        Default Configuration        =
=====================================*/

// Please use config.js to override these selectively:

var config = {
  dest: 'target/www',
  minify_images: true,

  vendor: {
    js: [
      './bower_components/jquery/dist/jquery.js',
      //'./bower_components/bootstrap/dist/js/bootstrap.js',
      './bower_components/angular/angular.js',
      './bower_components/angular-route/angular-route.js',
      './bower_components/angular-cookies/angular-cookies.js',
      // bower_components/angular-i18n/angular-locale_it-it.js
      './bower_components/ngstorage/ngStorage.js',
      './bower_components/angular-macgyver/lib/macgyver.js',
      './bower_components/datejs/build/date.js',
      './bower_components/datejs/build/date-it-IT.js',
//      './bower_components/angular-touch/angular-touch.js',
//      './bower_components/mobile-angular-ui/dist/js/mobile-angular-ui.js',
    ],

    fonts: [
      './bower_components/bootstrap/fonts/glyphicons-halflings-regular.*'
    ]
  },

  server: false,
};


if (require('fs').existsSync('./config.js')) {
  var configFn = require('./config');
  configFn(config);
};

/*-----  End of Configuration  ------*/


/*========================================
=            Requiring stuffs            =
========================================*/

var gulp           = require('gulp'),
    seq            = require('run-sequence'),
    //connect        = require('gulp-connect'),
    less           = require('gulp-less'),
    uglify         = require('gulp-uglify'),
    sourcemaps     = require('gulp-sourcemaps'),
    cssmin         = require('gulp-cssmin'),
    order          = require('gulp-order'),
    concat         = require('gulp-concat'),
    ignore         = require('gulp-ignore'),
    del            = require('del'),
    imagemin       = require('gulp-imagemin'),
    pngcrush       = require('imagemin-pngcrush'),
    templateCache  = require('gulp-angular-templatecache'),
    mobilizer      = require('gulp-mobilizer'),
    ngAnnotate     = require('gulp-ng-annotate'),
    replace        = require('gulp-replace'),
    ngFilesort     = require('gulp-angular-filesort'),
    streamqueue    = require('streamqueue'),
    rename         = require('gulp-rename'),
    path           = require('path'),
    spawn          = require('child_process').spawn;


/*================================================
=            Report Errors to Console            =
================================================*/

gulp.on('err', function(e) {
  console.log(e.err.stack);
});


/*=========================================
=            Clean dest folder            =
=========================================*/

gulp.task('clean', function (cb) {
  del([ config.dest ], cb);
});


/*==========================================
=            Start a web server            =
==========================================*/

var tornadoServer = null;

gulp.task('connect', function() {
	if (tornadoServer != null) {
		console.log('tornado server already running, restarting. killing-pid=', tornadoServer.pid);

		tornadoServer.kill();
	}

	tornadoServer = spawn('./src/main/python/gassman.py', [], {
		stdio: 'inherit',
	});

	tornadoServer.unref();

	console.log('started torndo server: pid=', tornadoServer.pid);
});

/*=====================================
=            Minify images            =
=====================================*/

gulp.task('images', function () {
  var stream = gulp.src('src/main/web/static/images/**/*')

  if (config.minify_images) {
    stream = stream.pipe(imagemin({
        progressive: true,
        svgoPlugins: [{removeViewBox: false}],
        use: [pngcrush()]
    }))
  };

  return stream.pipe(gulp.dest(path.join(config.dest, 'static/images')));
});


/*==================================
=            Copy fonts            =
==================================*/

gulp.task('fonts', function() {
  return gulp.src(config.vendor.fonts)
  .pipe(gulp.dest(path.join(config.dest, 'static/fonts')));
});


/*=================================================
=            Copy html files to dest              =
=================================================*/

gulp.task('html', function() {
  gulp.src(['src/main/web/**/*.html'])
  .pipe(gulp.dest(config.dest));
});


/*======================================================================
=            Compile, minify, mobilize less                            =
======================================================================*/

gulp.task('less', function () {
  gulp.src('./src/main/less/app.less')
    .pipe(less({
      paths: [ path.resolve(__dirname, 'src/main/less'), path.resolve(__dirname, 'bower_components') ]
    }))
    .pipe(mobilizer('app.css', {
      'app.css': {
        hover: 'exclude',
        //screens: ['0px']      
      },
      'hover.css': {
        hover: 'only',
        //screens: ['0px']
      }
    }))
    .pipe(cssmin())
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest(path.join(config.dest, 'static/css')));
});


/*====================================================================
=            Compile and minify js generating source maps            =
====================================================================*/
// - Orders ng deps automatically
// - Precompile templates to ng templateCache

gulp.task('js', function() {
    streamqueue({ objectMode: true },
      gulp.src(config.vendor.js),
      gulp.src('./src/main/web/**/*.js').pipe(ngFilesort()),
      gulp.src(['./src/main/templates/**/*.html',
                './src/main/web/static/partials/**/*.html'
                ]).pipe(templateCache({ module: 'gassmanApp' }))
    )
    .pipe(sourcemaps.init())
    .pipe(concat('app.js'))
    .pipe(ngAnnotate())
    .pipe(uglify())
    .pipe(rename({suffix: '.min'}))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(path.join(config.dest, 'static/js')));
});


/*===================================================================
=            Watch for source changes and rebuild/reload            =
===================================================================*/

gulp.task('watch', function () {
  if (typeof config.server) {
    gulp.watch([config.dest + '/**/*',
                './src/main/templates/**/*',
                './src/main/python/**/*'
                ], ['connect']);
  };
  // TODO: fonts?
  gulp.watch(['./src/main/web/static/partials/**/*'], ['html']);
  gulp.watch(['./src/main/less/**/*'], ['less']);
  gulp.watch(['./src/main/web/static/js/**/*',
              './src/main/templates/**/*',
              './src/main/web/static/partials/**/*',
              config.vendor.js
              ], ['js']);
  gulp.watch(['./src/main/web/static/images/**/*'], ['images']);
});

/*======================================
=            Build Sequence            =
======================================*/

gulp.task('build', function(done) {
  var tasks = ['html', 'fonts', 'images', 'less', 'js'];
  seq('clean', tasks, done);
});


/*====================================
=            Default Task            =
====================================*/

gulp.task('default', function(done){
  var tasks = [];

  if (typeof config.server) {
    tasks.push('connect');
  };

  tasks.push('watch');
  
  seq('build', tasks, done);
});
