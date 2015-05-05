/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.HomeSelectorController', [
    'gassmanServices'
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
		if (typeof(csaId) == 'string' && csaId)
			$location.path('/csa/' + csaId + "/detail");
		else
			$location.path('/person/' + $scope.profile.logged_user.id + '/detail');
	}).
	then (undefined, function (error) {
		$scope.error = error;
	});
}])
;
