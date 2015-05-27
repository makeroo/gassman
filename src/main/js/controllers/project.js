/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.ProjectController', [
	'GassmanApp.services.Gdata'
])

.controller('ProjectController', [
         '$scope', 'gdata',
function ($scope,   gdata) {
	$scope.version = null;

	gdata.sysVersion().
	then (function (r) {
		$scope.version = r.data[0];
	}); // non gestisco l'errore
}])
;
