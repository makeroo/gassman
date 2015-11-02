/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.HomeSelectorController', [
	'GassmanApp.services.Gdata'
])

.controller('HomeSelectorController', [
         '$scope', '$location', 'gdata',
function ($scope,   $location,   gdata) {
	$scope.error = null;

	gdata.profileInfo().
	then (function (profile) {
		$scope.profile = profile;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$location.path('/csa/' + csaId + "/detail");
	}).
	then (undefined, function (error) {
		if (error == gdata.error_codes.E_no_csa_found) {
			$location.path('/person/' + $scope.profile.logged_user.id + '/detail');
		} else {
			$scope.error = error;
		}
	});
}])
;
