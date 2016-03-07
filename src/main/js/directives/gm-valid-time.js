'use strict';

/**
 * Created by makeroo on 22/05/15.
 */

angular.module('GassmanApp.directives.GmValidTime', [
	'GassmanApp.services.Gdata'
])

.directive('gmValidTime', [
         'gdata', '$locale',
function (gdata,   $locale) {
	return {
		restrict: 'A',
		require: 'ngModel',
		link: function (scope, elem, attrs, ctrl) {
			ctrl.$parsers.push(function (value) {
//				scope.$parent.validEmail(value).

	            var timeFormat = $locale.DATETIME_FORMATS.shortTime;

	            var hs = moment(value, timeFormat, true);

				ctrl.$setValidity('valid-time', hs.isValid());

				return value;
			});
		}
	};
}])
;
