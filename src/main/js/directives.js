'use strict';

var gassmanDirectives = angular.module('gassmanDirectives', [
    'gassmanServices'
    ]);

/*
var FLOAT_REGEXP = /^\-?\d+((\.|\,)\d+)?$/;
app.directive('smartFloat', function() {
  return {
    require: 'ngModel',
    link: function(scope, elm, attrs, ctrl) {
      ctrl.$parsers.unshift(function(viewValue) {
        if (FLOAT_REGEXP.test(viewValue)) {
          ctrl.$setValidity('float', true);
          return parseFloat(viewValue.replace(',', '.'));
        } else {
          ctrl.$setValidity('float', false);
          return undefined;
        }
      });
    }
  };
});
*/



gassmanDirectives.directive('requiredAccount', function () {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
            scope.$watch(attrs.ngModel,
            function (value) {
                var valid = (typeof(value) == 'number');
                ctrl.$setValidity('accountDefined', valid);
                //console.log('gmacc2 value: ', value);
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
});
/*
gassmanDirectives.directive('checkCurrencies', function () {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
            scope.$watch(attrs.ngModel,
            function (value) {
                var valid = (typeof(value) == 'number');
//    			ctrl.$setValidity('accountDefined', valid);

                if (valid)
                    scope.checkCurrencies();
            }
            );
        }
    };
});
*/
;
