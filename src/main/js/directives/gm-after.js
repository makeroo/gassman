'use strict';

/**
 * Created by makeroo on 22/05/15.
 */

angular.module('GassmanApp.directives.GmAfter', [
	'GassmanApp.services.Gdata'
])

.directive('gmAfter', [
         'gdata', '$locale', '$parse',
function (gdata,   $locale,   $parse) {
	return {
		restrict: 'A',
		require: 'ngModel',
		link: function (scope, elem, attrs, ctrl) {
            var guardExpr = $parse(attrs.gmAfter);
            var valueExpr = $parse(attrs.ngModel);

			function parseTime (s) {
	            var timeFormat = $locale.DATETIME_FORMATS.shortTime;
	            var hs = moment(s, timeFormat, true);

				return hs;
			}

			scope.$watch(function () {
                var guard = guardExpr(scope);
                var value = valueExpr(scope);

				return parseTime(value) > parseTime(guard);
			},
			function (value) {
                ctrl.$setValidity('after', value);
			});
		}
	};
}])
;
