/**
 * Created by makeroo on 26/05/15.
 */

angular.module('GassmanApp.directives.GmRequiredAccount', [
    ])

.directive('gmRequiredAccount', function () {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
            scope.$watch(attrs.ngModel,
            function (value) {
                var valid = (typeof(value) == 'number');
                ctrl.$setValidity('accountDefined', valid);
            }
            );
            /* non viene invocato quando svuoto
            ctrl.$parsers.push(function (value) {
                //console.log('checking match:', value, scope.trans.clients[0]);


                console.log('gmaccount 2 parser: ', value);
                var empty = !value;

                ctrl.$setValidity('accountDefined', !empty);

                if (!empty)
                    scope.checkCurrencies();

                return value;
            });
            */
        }
    };
})
;
