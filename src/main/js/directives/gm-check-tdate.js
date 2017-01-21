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
                    if (!tline) return true;

                    var account_id = tline.account;

                    if (!account_id) return true;

                    var valid_from = scope.currencies[account_id].valid_from;

                    return !valid_from || valid_from < value;
                }

                var date_is_valid = true;

                angular.forEach(scope.trans.producers, function (p) {
                    if (!check_date(p)) {
                        date_is_valid = false;
                        // TODO: qui mi dovrei interrompere
                        // oppure, invece di mettere errore sulla data potrei metterla
                        // su ogni produttore "nuovo" così da indicare quali sono
                    }
                });

                angular.forEach(scope.trans.clients, function (p) {
                    if (!check_date(p)) {
                        date_is_valid = false;
                        // TODO: qui mi dovrei interrompere
                        // oppure, invece di mettere errore sulla data potrei metterla
                        // su ogni produttore "nuovo" così da indicare quali sono
                    }
                });

                ctrl.$setValidity('trans_date', date_is_valid);

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
