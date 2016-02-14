/**
 * Created by makeroo on 12/02/16.
 */

'use strict';

angular.module('GassmanApp.controllers.CookieBanner', [
    'GassmanApp.services.Gstorage'
])

.controller('CookieBanner', [
         '$scope', '$rootScope', 'gstorage',
function ($scope,   $rootScope,   gstorage) {
//    var cookieConsent = gstorage.cookieConsent();
    $rootScope.cookieBanner = gstorage.cookieBanner();

    $scope.optout = function () {
        $rootScope.cookieBanner = 'out';
    };

    $scope.accept = function () {
        $rootScope.cookieBanner = gstorage.cookieBanner('hide');
    };

    $scope.reconsider = function () {
        $rootScope.cookieBanner = 'show';
    };
}])
;
