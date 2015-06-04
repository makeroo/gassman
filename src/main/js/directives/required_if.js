/**
 * Created by makeroo on 26/05/15.
 */

'use strict';

angular.module('GassmanApp.directives.RequiredIf', [
    ])

.directive('requiredIf', [
         '$parse',
function ($parse) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
            var guardExpr = $parse(attrs.requiredIf);
            var valueExpr = $parse(attrs.ngModel);

            scope.$watch(function () {
                var guard = guardExpr(scope);
                var value = valueExpr(scope);
                var valid = !guard || !!value;

                //console.log('requiredIf on ', elem, 'guard:', guard, 'value:', value, 'valid:', valid);

                return valid;
            },
            function (value) {
                ctrl.$setValidity('required', value);
            });
/*
            ctrl.$parsers.push(function (value) {
                //console.log('checking match:', value, scope.l)
                //console.log(scope.l, scope.$parent.autocompletionData);
                var acd = scope.$parent.autocompletionData;
                var empty = !value;
                var f = empty;

                if (!f)
                    for (var i in acd) {
                        var acl = acd[i];
                        if (acl.name == value) {
                            scope.l.account = acl.acc;
                            f = true;
                            break;
                        }
                    }

                ctrl.$setValidity('accountMatch', f);

                if (!f || empty) {
                    //console.log('not found, resetting account');
                    scope.l.account = null;
                } else {
                    //console.log('found, account defined')
                    scope.$parent.checkCurrencies();
                }

                //console.log('returning value', typeof(value), scope.l);
                return value;
            });
*/
/*    		ctrl.$parsers.push(function (value) {
                return accountDefined(value, scope.l.amount);
            });*/
        }
    };
}])
;
