'use strict';

angular.module('GassmanApp.directives.WhenScrolled', [
    ])

.directive('whenScrolled', [
         '$window', '$document',
function ($window,   $document) {
	return function (scope, elm, attr) {
		//var raw = elm[0];
        var trigger = parseInt(attr.whenScrolledPixels) || 300;
        var w = $($window);

		w.bind('scroll', function() {
            console.log('scrolling: winScrollTop=', w.scrollTop, 'height=', w.height(), 'docHeight=', $document.height(), 'trigger=', trigger);
            if (w.scrollTop() + w.height() >= $document.height() - trigger) {
                //vecchio if: (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
		});
	};
}])
;
