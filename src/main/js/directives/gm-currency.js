'use strict';

/**
 * Created by makeroo on 22/05/15.
 */

angular.module('GassmanApp.directives.GmCurrency', [
    ])

.directive('gmCurrency', [
		 '$parse',
function ($parse) {
    var FLOAT_REGEXP = /^\-?\d+((\.|\,)\d+)?$/;

    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
/*    		var accountDefined = function (account, amount) {
                //console.log('amount: checking defined:', account, amount, scope.l)

                ctrl.$setValidity('required', !( account && !amount ));

                return amount;
            };
*/
			var decimalsExpr = $parse(attrs.gmCurrency);
            var decimals = decimalsExpr(scope);
/*
            scope.$watch(function () {
                return scope.l.account;
            },
            function (value) {
                accountDefined(value, scope.l.amount);
            }
            );
*/
            ctrl.$parsers.push(function (value) {
                if (value == '') {
                    ctrl.$setValidity('number', true);
                    return null;
                } else if (FLOAT_REGEXP.test(value)) {
                    ctrl.$setValidity('number', true);
                    return value;
                } else {
                    ctrl.$setValidity('number', false);
                    return null;
                }
            });

            ctrl.$parsers.push(function (value) {
                if (value == null) {
                    // se non è un numero resetto gli altri controlli
                    // TODO: usare gmMessages invece
                    ctrl.$setValidity('positive', true);
                    ctrl.$setValidity('decimals', true);
                    return value;
                }

                var f = parseFloat(value.replace(',', '.'));
                var p = f > 0.0;
                ctrl.$setValidity('positive', f);

                if (!p)
                    // non faccio controlli multipli
                    return value;

                var x = f * Math.pow(10.0, decimals);
                var d = x - Math.floor(x + .5) < .05;

                ctrl.$setValidity('decimals', d);

                return value;
            });
/*
            ctrl.$parsers.push(function (value) {
                return accountDefined(scope.l.account, value);
            });*/
        }
    };
}])
;
