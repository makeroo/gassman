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

    gdata.profileInfo().
    then (function (profile) {
        $scope.profile = profile;

        return gdata.selectedCsa();
    }).
    then (function (csaId) {
        var u = gstorage.popRequestedUrl();

        $location.path(u || '/csa/' + csaId + "/detail");
    }).
    then (undefined, function (error) {
        if (error[0] == gdata.error_codes.E_not_authenticated) {
            $location.path('/login');
        } else if (error[0] == gdata.error_codes.E_no_csa_found) {
            $location.path('/person/' + $scope.profile.logged_user.id + '/detail');
        } else {
            $scope.error = error;
        }
    });
}])
;
