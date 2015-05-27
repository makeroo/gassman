'use strict';

/**
 * Created by makeroo on 22/05/15.
 */

angular.module('GassmanApp.directives.GmUniqueEmail', [
	'GassmanApp.services.Gdata'
])

.directive('gmUniqueEmail', [
         'gdata',
function (gdata) {
	return {
		restrict: 'A',
		require: 'ngModel',
		link: function (scope, elem, attrs, ctrl) {
			ctrl.$parsers.push(function (value) {
//				scope.$parent.validEmail(value).
				var csaId = scope.$parent.csaId;
				var pid = scope.$parent.personProfile.profile.id;

				if (ctrl.$error.email) {
					ctrl.$setValidity('unique', true);
					return value;
				}

				gdata.uniqueEmail(csaId, pid, value).
				then (function (r) {
					var res = r.data == 0;

					ctrl.$setValidity('unique', res);
				}).
				then (undefined, function (error) {
					console.log('gmUniqueEmail: server error, email not checked:', error);

					ctrl.$setValidity('unique', false);
				});
				return value;
			});
		}
	};
}])
;
