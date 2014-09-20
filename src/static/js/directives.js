var gassmanDirectives = angular.module('gassmanDirectives', [
    'gassmanServices'
    ]);

gassmanDirectives.directive('gmUnique', function (gdata) {
	return {
		restrict: 'A',
		require: 'ngModel',
		link: function (scope, elem, attrs, ctrl) {
			ctrl.$parsers.push(function (value) {
//				scope.$parent.validEmail(value).
				var csaId = scope.$parent.csaId;
				var pid = scope.$parent.personProfile.profile.id;

				if (ctrl.$error.email) {
					ctrl.$setValidity('unique', true);
					return value;
				}

				gdata.uniqueEmail(csaId, pid, value).
				then (function (r) {
					var res = r.data == 0;

					ctrl.$setValidity('unique', res);
				}).
				then (undefined, function (error) {
					console.log('gmUnique: server error, email not checked:', error);

					ctrl.$setValidity('unique', false);
				});
				return value;
			});
		}
	};
});

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

gassmanDirectives.directive('gmAccount', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var accountDefined = function (account, amount) {
    			//console.log('checking defined:', account, amount, scope.l)

    			ctrl.$setValidity('amountWithoutAccount', !( !account && amount > 0 ));

    			return account;
    		};

    		scope.$watch(function () {
    			return scope.l.amount;
    		},
    		function (value) {
    			accountDefined(scope.l.accountName, value);
    		}
    		);

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

    		ctrl.$parsers.push(function (value) {
    			return accountDefined(value, scope.l.amount);
    		});
    	}
    };
});

gassmanDirectives.directive('gmAccount2', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		ctrl.$parsers.push(function (value) {
    			//console.log('checking match:', value, scope.trans.clients[0]);

    			//console.log(scope.l, scope.$parent.autocompletionData);
    			var acd = scope.autocompletionData;
    			var empty = !value;
    			var f = empty;

    			if (!f)
    				for (var i in acd) {
    					var acl = acd[i];
    					if (acl.name == value) {
    						f = true;
    						scope.trans.clients[0].account = acl.acc;
    						break;
    					}
    				}

    			ctrl.$setValidity('accountMatch', f);
    			ctrl.$setValidity('accountDefined', !empty);

    			if (!f || empty)
    				scope.trans.clients[0].account = null;
    			else
    				scope.checkCurrencies();

    			return value;
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
    			//console.log('checking expense:', desc, amount, scope.l)

    			ctrl.$setValidity('amountWithoutNotes', !( !desc && amount > 0 ));
//    			ctrl.$setValidity('amountDefined', !( desc && !amount ));

    			return desc;
    		};

    		scope.$watch(function () {
    			return scope.l.amount;
    		},
    		function (value) {
    			descDefined(scope.l.notes, value);
    		}
    		);

    		ctrl.$parsers.push(function (value) {
    			return descDefined(value, scope.l.amount);
    		});
    	}
    };
});
gassmanDirectives.directive('gmAmount2', function () {
    return {
    	restrict: 'A',
    	require: 'ngModel',
    	link: function (scope, elem, attrs, ctrl) {
    		var descDefined = function (desc, amount) {
    			//console.log('checking expense:', desc, amount, scope.l)

//    			ctrl.$setValidity('amountWithoutNotes', !( !desc && amount > 0 ));
    			ctrl.$setValidity('notesWithoutAmount', !( desc && !amount ));

    			return amount;
    		};

    		scope.$watch(function () {
    			return scope.l.notes;
    		},
    		function (value) {
    			descDefined(value, scope.l.amount);
    		}
    		);

    		ctrl.$parsers.push(function (value) {
    			if (ctrl.$error.number || value === null) {
    				// se non è un numero resetto gli altri controlli
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
    			return descDefined(scope.l.notes, value);
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
