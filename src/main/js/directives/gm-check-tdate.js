'use strict';

/**
 * Created by makeroo on 22/05/15.
 */

angular.module('GassmanApp.directives.GmCheckTdate', [
    ])

.directive('gmCheckTdate', [
		 '$parse',
function ($parse) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {

            function tdate_parser (value) {

                function check_date (tline) {
                    if (!tline) return 0;

                    var account_id = tline.account;

                    if (!account_id) return 0;

                    var account = scope.currencies[account_id];

                    if (!account) {
                        // sto modificando una transazione fra le cui righe si sta riferendo
                        // un conto adesso chiuso...
                        var r = 2;

                        angular.forEach(tline.accountNames, function (account_name) {
                            if (value > account_name.valid_to) {
                                r = 2;
                            } else if (value < account_name.valid_from) {
                                r = 1;
                            } else {
                                // mi basta che almeno uno sia valido
                                r = 0;
                            }
                        });

                        return r;
                    }

                    var valid_from = account.valid_from;

                    return valid_from && valid_from > value ? 1 : 0;
                }

                var date_is_valid = 0;

                angular.forEach(scope.trans.producers, function (p) {
                    date_is_valid |= check_date(p);

                    // invece di mettere errore sulla data potrei metterla
                    // su ogni produttore "nuovo" così da indicare quali sono
                });

                angular.forEach(scope.trans.clients, function (p) {
                    date_is_valid |= check_date(p);

                    // invece di mettere errore sulla data potrei metterla
                    // su ogni produttore "nuovo" così da indicare quali sono
                });

                ctrl.$setValidity('trans_date_below', !(date_is_valid & 1));
                ctrl.$setValidity('trans_date_above', !(date_is_valid & 2));

                return value;
            }

            ctrl.$parsers.push(tdate_parser);

            scope.$watch(function () {
                return scope.trans.producers;
            }, function () {
                tdate_parser(scope.trans.tdate);
            }, true);

            scope.$watch(function () {
                return scope.trans.clients;
            }, function () {
                tdate_parser(scope.trans.tdate);
            }, true);
        }
    };
}])
;
