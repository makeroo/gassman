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

    this.selectedCsa = function (csaId) {
        var pi = $rootScope.gassman.loggedUser;

        if (!pi) {
            return null;
        }

        if (csaId === undefined) {
            // restituisce il csa selezionato

            var x = $localStorage.selectedCsa;

            if (x === undefined || !(x in pi.csa)) {
                x = null;
                for (var i in pi.csa) {
                    if (!pi.csa.hasOwnProperty(i)) {
                        continue;
                    }
                    x = i;
                    break;
                }

                if (x !== null) {
                    $localStorage.selectedCsa = x;
                    return x;
                } else {
                    return null;
                }
            } else {
                return x;
            }
        } else {
            // imposta il csa selezionato

            if (csaId in pi.csa) {
                $localStorage.selectedCsa = csaId;

                return csaId;
            } else {
                return null;
            }
        }
    };
}])
;
