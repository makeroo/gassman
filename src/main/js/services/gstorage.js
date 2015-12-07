/**
 * Created by makeroo on 01/12/15.
 */

'use strict';

angular.module('GassmanApp.services.Gstorage', [
    'ngCookies',
    'ngStorage'
])

.service('gstorage', [
         '$localStorage', '$rootScope',
function ($localStorage,   $rootScope) {
    var gstorage = this;

    function update (f) {
        var g = $localStorage.gassman;

        if (!g) {
            g = {};
        }

        if (f) {
            f(g);
        }

        $localStorage.gassman = g;

        return g;
    }

    this.saveRequestedUrl = function (u) {
        update(function (g) {
            g.requestedUrl = u;
        });
    };

    this.popRequestedUrl = function () {
        var r;

        update(function (g) {
            r = g.requestedUrl;

            g.requestedUrl = null;
        });

        return r;
    };
}])
;
