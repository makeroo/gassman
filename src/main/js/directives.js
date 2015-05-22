'use strict';

var gassmanDirectives = angular.module('gassmanDirectives', [
    'gassmanServices'
    ]);


gassmanDirectives.directive('gmAmount', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var accountDefined = function (account, amount) {
    			//console.log('amount: checking defined:', account, amount, scope.l)

    			ctrl.$setValidity('accountWithoutAmount', !( account && !amount ));

    			return amount;
    		};

    		scope.$watch(function () {
    			return scope.l.account;
    		},
    		function (value) {
    			accountDefined(value, scope.l.amount);
    		}
    		);

    		ctrl.$parsers.push(function (value) {
    			if (ctrl.$error.number || value === null) {
    				// se non è un numero resetto gli altri controlli
    				// TODO: usare gmMessages invece
    				ctrl.$setValidity('positive', true);
    				ctrl.$setValidity('decimals', true);
    				return value;
    			}

    			var f = value > 0;
				ctrl.$setValidity('positive', f);

				if (!f)
					// non faccio controlli multipli
					return value;

				var dd = Math.pow(10, 2); // TODO: fare che 2 dipende dalla currency
				var x = value * dd;
				f = x - Math.floor(x + .5) < .05;

				ctrl.$setValidity('decimals', f);

				return value;
    		});

    		ctrl.$parsers.push(function (value) {
    			return accountDefined(scope.l.account, value);
    		});
    	}
    };
});

gassmanDirectives.directive('required-if', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var accountDefined = function (account, amount) {
    			//console.log('checking defined:', account, amount, scope.l)

    			ctrl.$setValidity('amountWithoutAccount', !( !account && amount > 0 ));

    			return account;
    		};

    		scope.$watch(attrs.requiredIf,
    		function (value) {
    			accountDefined(attrs.ngModel, value);
    		}
    		);
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
    		ctrl.$parsers.push(function (value) {
    			return accountDefined(value, scope.l.amount);
    		});
    	}
    };
});

gassmanDirectives.directive('requiredAccount', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		scope.$watch(attrs.ngModel,
    		function (value) {
				var valid = (typeof(value) == 'number');
    			ctrl.$setValidity('accountDefined', valid);
    			console.log('gmacc2 value: ', value);
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
