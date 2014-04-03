'use strict';

var gassmanControllers = angular.module('gassmanControllers', []);

gassmanControllers.controller('MenuController', function($scope, $filter, gdata) {
	$scope.profile = null;
	$scope.profileError = null;
	$scope.functions = [];
	$scope.totalAmount = null;
	$scope.totalAmountError = null;
	$scope.amount = null;
	$scope.amountError = null;
	$scope.currencySymbol = null;
	$scope.amountClass = null;

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;

		for (var i in gassmanApp.functions) {
			var f = gassmanApp.functions[i];

			if (pData.permissions.indexOf(f.p) != -1 ||
				('e' in f && f.e(pData.permissions))) {
				$scope.functions.push(f);

				if ('justAdded' in f)
					f.justAdded($scope, gdata);
			}
		}
	}).
	then (undefined, function (error) {
		$scope.profileError = error;
	});

	gdata.selectedCsa().
	then (function (csaId) { return gdata.accountByCsa(csaId); }).
	then (function (accId) { return gdata.accountAmount(accId); }).
	then (function (r) {
		$scope.amount = parseFloat( r.data[0] );
		$scope.currencySymbol = r.data[1];

		$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
	}).
	then (undefined, function (error) { $scope.amountError = error.data; })/*.
	done()*/;
});

gassmanControllers.controller('AccountDetails', function($scope, $filter, $routeParams, $location, gdata) {
	$scope.movements = [];
	$scope.movementsError = null;
	$scope.transaction = null;
	$scope.transactionError = null;
	$scope.accountOwner = null;
	$scope.accountOwnerError = null;
//	$scope.selectedMovement = null;

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var accId = $routeParams['accountId'];
	var start = 0;
	var blockSize = 25;
	var concluded = false;

	var showOwner = function (accId) {
		$scope.accId = accId;
		gdata.accountOwner(accId).
		then (function (r) {
			$scope.accountOwner = r.data;
		}).
		then (undefined, function (error) {
			$scope.accountOwnerError = error.data;
		});
	};

	gdata.selectedCsa().
	then (function (csaId) { $scope.csaId = csaId; return accId || gdata.accountByCsa(csaId); }).
	then (function (accId) {
		showOwner(accId);
		$scope.loadMore(); }).
	then (undefined, function (error) { $scope.accountOwnerError = error.data; });

	$scope.transactionAccount = function (accId) {
		try {
			var p = $scope.transaction.people[accId];
			if (p)
				// p: [id, fist, middle, last, accId]
				return p[1] + (p[2] ? ' ' + p[2] : '') + ' ' + p[3];
			var n = $scope.transaction.accounts[accId];
			return n ? n : 'N/D';
		} catch (e) {
			return 'N/D';
		}
	};

	$scope.showTransaction = function (mov) {
		$scope.transaction = null;
		$scope.transactionError = null;
//		$scope.selectedMovement = mov[4];
		gdata.transactionDetail($scope.csaId, mov[4]).
		then (function (r) {
			r.data.mov = mov;
			$scope.transaction = r.data;
		}).
		then (undefined, function (error) {
			$scope.transactionError = error.data;
		});
	};

	$scope.loadMore = function () {
		if (concluded) return;

		gdata.accountMovements($scope.accId, start, blockSize).
		then (function (r) {
			concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.movements = $scope.movements.concat(r.data);
		}).
		then (undefined, function (error) {
			concluded = true;
			$scope.serverError = error.data[1];
			console.log('movements error:', error.data)
			$scope.showErrorMessage = false;
			$scope.movementsError = error.data;
			//console.log('error', data, status, headers, config);
		});
	};
});

gassmanControllers.controller('AccountsIndex', function($scope, $filter, $location, gdata) {
	$scope.accounts = [];
	$scope.accountsError = null;

	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.loadMore = function () {
		if (concluded) return;

		gdata.selectedCsa().
		then (function (csaId) { return gdata.accountsIndex(csaId, start, blockSize); }).
		then(function (r) {
			concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.accounts = $scope.accounts.concat(r.data);
		}).
		then (undefined, function (error) {
			concluded = true;
			$scope.accountsError = error.data;
		});
	};

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/details');
	};

	$scope.loadMore();
});

gassmanControllers.controller('TransactionDeposit', function($scope, $routeParams, gdata) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.totalAmount = 0.0;
	$scope.confirmDelete = false;
	$scope.currency = '';
	$scope.autocompletionData = [];
	$scope.autocompletionDataError = null;

	var newLine = function () {
		return {
			name: '',
			amount: '',
			notes: '',
			nameClass: '',
			amountClass: ''
		};
	};

	$scope.checkLine = function (e) {
		$scope.lines.push(newLine());
	};

	$scope.updateTotalAmount = function () {
		var t = 0.0;
		for (var i in $scope.lines) {
			var l = $scope.lines[i];
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		}

		$scope.totalAmount = t;
	}

	$scope.saveDeposit = function () {
		var data = {
			id: $scope.transId,
			cc_type: 'D',
			lines: []
		};

		for (var i in $scope.lines) {
			var l = $scope.lines[i];

			if (l.amount > 0.0) {
				if (l.name) {
					l.nameClass = '';
					data.lines.push(l);
				} else {
					l.nameClass = 'required';
					// TODO: errore

					return;
				}
				l.amountClass = '';
			} else if (l.amount < 0.0) {
				l.amountClass = 'negative';
			} else {
				l.nameClass = '';
				l.amountClass = '';
			}
		}

		//data = angular.toJson(data)
		gdata.transactionSave(csaId, data)
		then (function (r) {
			
		}).
		then (undefined, function (error) {
			
		});
		// TODO: salva transazione
	};

	$scope.confirmCancelDeposit = function () {
		$scope.confirmDelete = true;
	};

	$scope.cancelDeposit = function () {
		$scope.confirmDelete = false;

		// TODO: cancella transazione
	}

	if ($scope.transId == undefined) {
		$scope.lines.push(newLine());
	} else {
		// TODO: carica la transazione
	}

	gdata.selectedCsa().
	then (function (csaId) { return gdata.ccountsNames(csaId); }).
	then (function (r) {
		// trasforma data in autocompletionData
		var accountNames = r.data.accountNames;
		var accountPeople = r.data.accountPeople;
		var accountPeopleAddresses = r.data.accountPeopleAddresses;
		var people = {};
		for (var i in accountNames) {
			var o = accountNames[i];
			// o è un array gc_name, accId
			$scope.autocompletionData.push({ name: o[0], acc: o[1] });
		}
		for (var i in accountPeople) {
			var o = accountPeople[i];
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + ' ' + (o[2] || '') + ' ' + (o[3] || '');
			n = n.trim();
			people[o[0]] = n;
			$scope.autocompletionData.push({ name: n, acc: o[4], p: o[0] });
		}
		for (var i in accountPeopleAddresses) {
			var o = accountPeopleAddresses[i];
			// o è un array 0:addr 1:pid 2:accId
			var n = o[0] + ' (' + people[o[1]] + ')';
			$scope.autocompletionData.push({ name: n, acc: o[2], p: o[1] });
		}
	}).
	then (undefined, function (error) {
		$scope.autocompletionDataError = error.data;
	});
});

gassmanControllers.controller('TransactionPayment', function() {
});

gassmanControllers.controller('TransactionsIndex', function() {
});

gassmanControllers.controller('HelpController', function() {
});

gassmanControllers.controller('FaqController', function() {
});

gassmanControllers.controller('ProjectController', function($scope, gdata) {
	$scope.version = null;

	gdata.sysVersion().
	then (function (r) {
		$scope.version = r.data[0];
	}); // non gestisco l'errore
});
