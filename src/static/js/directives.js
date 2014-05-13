var gassmanDirectives = angular.module('gassmanDirectives', []);

gassmanDirectives.directive('gmAmount', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		ctrl.$parsers.push(function (value) {
    			if (ctrl.$error.number || value === null) {
    				// se non è un numero resetto gli altri controlli
    				ctrl.$setValidity('positive', true);
    				ctrl.$setValidity('decimals', true);
    				return;
    			}

    			var f = value > 0;
				ctrl.$setValidity('positive', f);

				if (!f)
					// non faccio controlli multipli
					return null;

				var dd = Math.pow(10, 2); // TODO: fare che 2 dipende dalla currency
				var x = value * dd;
				f = x - Math.floor(x + .5) < .05;

				ctrl.$setValidity('decimals', f);

				return f ? value : null;
    		});
    	}
    };
});

gassmanDirectives.directive('gmAccount', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var accountDefined = function (account, amount) {
    			console.log('checking defined:', account, amount, scope.l)
    			var f = amount == '' || amount == null || (account && amount > 0);
    			ctrl.$setValidity('accountDefined', f);

    			return f ? account : null;
    		};

    		scope.$watch(function () {
    			return scope.l.amount;
    		},
    		function (value) {
    			accountDefined(scope.l.accountName, value);
    		}
    		);

    		ctrl.$parsers.push(function (value) {
    			console.log('checking match:', value, scope.l)
    			//console.log(scope.l, scope.$parent.autocompletionData);
    			var acd = scope.$parent.autocompletionData;
    			var empty = !value;
    			var f = empty;

    			if (!f)
    				for (var i in acd) {
    					var acl = acd[i];
    					if (acl.name == scope.l.accountName) {
    						f = true;
    						break;
    					}
    				}

    			ctrl.$setValidity('accountMatch', f);

    			if (!f || empty)
    				scope.l.account = null;

    			return value;
    		});

    		ctrl.$parsers.push(function (value) {
    			accountDefined(value, scope.l.amount);
    		});
    	}
    };
});

gassmanDirectives.directive('gmExpense', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var descDefined = function (desc, amount) {
    			console.log('checking expense:', desc, amount, scope.l)
    			var f = amount == '' || amount == null || (desc && amount > 0);
    			ctrl.$setValidity('expenseDefined', f);

    			return f ? desc : null;
    		};

    		scope.$watch(function () {
    			return scope.l.amount;
    		},
    		function (value) {
    			descDefined(scope.l.notes, value);
    		}
    		);

    		ctrl.$parsers.push(function (value) {
    			descDefined(value, scope.l.amount);
    		});
    	}
    };
});

gassmanDirectives.directive('whenScrolled', function() {
	return function (scope, elm, attr) {
		var raw = elm[0];

		elm.bind('scroll', function() {
			if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
				scope.$apply(attr.whenScrolled);
			}
		});
	};
});
