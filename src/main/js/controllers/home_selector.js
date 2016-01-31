/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.HomeSelectorController', [
    'GassmanApp.services.Gdata',
    'GassmanApp.services.Gstorage'
])

.controller('HomeSelectorController', [
         '$scope', '$location', 'gdata', 'gstorage',
function ($scope,   $location,   gdata,   gstorage) {
    $scope.error = null;

    if (!$scope.gassman.loggedUser) {
        $location.path('/login');

        return;
    }

    var u = gstorage.popRequestedUrl();

    if (u) {
        $location.path(u);

        return;
    }

    if ($scope.gassman.selectedCsa) {
        $location.path('/csa/' + $scope.gassman.selectedCsa + "/detail");

        return;
    }

    $location.path('/person/' + $scope.gassman.loggedUser.profile.id + '/detail');
}])
;
