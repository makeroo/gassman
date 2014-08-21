'use strict';

var gassmanControllers = angular.module('gassmanControllers', [
    'gassmanServices',
    'gassmanDirectives',
    'Mac'
    ]);

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
	$scope.csaId = null;
	$scope.accountId = null;

	var reloadAmounts = function () {
		gdata.accountAmount($scope.accountId).
		then (function (r) {
			$scope.amountError = null;
			$scope.amount = parseFloat( r.data[0] );
			$scope.currencySymbol = r.data[1];

			$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
		}).
		then (undefined, function (error) {
			$scope.amount = null;
			$scope.currencySymbol = null;
			$scope.amountError = error.data;
		})/*.
		done()*/;

		if ($scope.profile.permissions.indexOf(gassmanApp.P_canCheckAccounts) == -1) {
			$scope.totalAmountError = null;
			$scope.totalAmount = null;
		} else {
			gdata.totalAmount($scope.csaId).
			then(function (r) {
				$scope.totalAmountError = null;
				$scope.totalAmount = r.data;
			}).
			then (undefined, function (error) {
				$scope.totalAmount = null;
				$scope.totalAmountError = error;
			});
		}
	};

	$scope.$on('AmountsChanged', function () {
		reloadAmounts();
	});

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

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;
		return gdata.accountByCsa(csaId);
	}).
	then (function (accId) {
		$scope.accountId = accId;
		reloadAmounts();
	}).
	then (undefined, function (error) {
		$scope.profileError = error;
	});
});

gassmanControllers.controller('AccountDetails', function($scope, $filter, $routeParams, gdata) {
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
			return n ? n[0] : 'N/D';
		} catch (e) {
			return 'N/D';
		}
	};

	$scope.transactionCurrency = function (accId) {
		try {
			var n = $scope.transaction.accounts[accId];
			return n ? n[1] : '';
		} catch (e) {
			return '';
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
			// TODO: FIXME: qui ho 2 errori...
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
	$scope.queryFilter = '';
	$scope.queryOrder = 0;
	$scope.profile = null;
	$scope.profileError = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = '';
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;

		reset();
		$scope.loadMore();
	};

	var reset = function () {
		$scope.accounts = [];
		$scope.accountsError = null;
		start = 0;
		$scope.concluded = false;
	};

	var currCsa = null;

	$scope.loadMore = function () {
		if ($scope.concluded) return;

		gdata.accountsIndex(currCsa, lastQuery, lastQueryOrder, start, blockSize).
		then(function (r) {
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.accounts = $scope.accounts.concat(r.data);

			angular.forEach(r.data, function (e) {
				e.accountData = !!e[4];
			});

			if ($scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) == -1)
				return;

			angular.forEach(r.data, function (e) {
				if (e.profile)
					return;
				var pid = e[0];
				gdata.profile(currCsa, pid).
				then(function (p) {
					e.profile = p;
				});
			});
		}).
		then (undefined, function (error) {
			$scope.concluded = true;
			$scope.accountsError = error.data;
		});
	};

	$scope.showAccount = function (accountId, personId) {
		if ($scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) == -1) {
			$location.path('/account/' + accountId + '/details');
		} else {
			$location.path('/person/' + personId + '/details');
		}
	};

	gdata.selectedCsa().
	then (function (csaId) {
		currCsa = csaId;
		return gdata.profileInfo();
	}).
	then (function (pData) {
		$scope.profile = pData;
		$scope.loadMore();
	}).
	then (undefined, function (error) {
		$scope.profileError = error.data;
	});
});

gassmanControllers.controller('TransactionDeposit', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.tdate = new Date();
	$scope.tdesc = 'Accredito';
	$scope.totalAmount = 0.0;
	$scope.confirmDelete = false;
	$scope.currency = null;
	$scope.currencyError = false;
	$scope.currencies = {};
	$scope.autocompletionData = [];
	$scope.autocompletionDataError = null;
	$scope.csaId = null;
	$scope.tsaveOk = null;
	$scope.tsaveError = null;

	var newLine = function () {
		return {
			accountName: '',
			account: null,
			amount: '',
			notes: ''
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
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.transId == 'new' ? null : $scope.transId,
			cc_type: 'd',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.tdate,
			description: $scope.tdesc
		};

		for (var i in $scope.lines) {
			var l = $scope.lines[i];

			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		}

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.newTrans = function () {
		$scope.tdate = new Date();
		$scope.tdesc = 'Accredito';
		$scope.totalAmount = 0.0;
		$scope.confirmDelete = false;
		$scope.currency = null;
		$scope.tsaveOk = null;
		$scope.lines.push(newLine());
	};

	$scope.viewLastTrans = function () {
		$location.path('/transaction/' + $scope.savedTransId + '/d');
	};

	$scope.confirmCancelDeposit = function () {
		$scope.confirmDelete = true;
		$timeout(function () { $scope.confirmDelete = false; }, 3200.0);
	};

	$scope.cancelDeposit = function () {
		$scope.confirmDelete = false;

		var data = {
				transId: $scope.transId,
				cc_type: 't',
				currency: $scope.currency[0],
				lines: [],
				date: $scope.tdate,
				description: $scope.tdesc
			};

		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		for (var i in $scope.lines) {
			var l = $scope.lines[i];
			var a = l.account;

			if (!a)
				continue;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr.cur;
			} else if (!angular.equals($scope.currency, curr.cur)) {
				$scope.currency = null;
				$scope.currencyError = true;
				return;
			}
		}

		$scope.currencyError = false;
	};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.accountsNames($scope.csaId);
	}).then (function (r) {
		// trasforma data in autocompletionData

		$scope.currencies = accountAutocompletion.parse(r.data);

		$scope.autocompletionData = accountAutocompletion.compose($scope.currencies);

		if ($scope.transId == 'new')
			return {
				data: {
				transId: 'new',
				description: 'Accredito',
				date: new Date(),
				cc_type: 'd',
				currency: null,
				lines: []
			} };
		else
			return gdata.transactionForEdit($scope.csaId, $scope.transId);
	}).then(function (tdata) {
		var t = tdata.data;

		if (t.cc_type != 'd')
			throw "illegal type";

		$scope.transId = t.transId;
		$scope.tdesc = t.description;
		$scope.tdate = new Date(t.date);

		// caricata quindi rimuovo la riga negativa
		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);

			//console.log(x, typeof(x));
			if (x < 0) {
				t.lines.splice(i, 1);
			} else {
				l.amount = x;
			}
		}

		for (var i in t.lines) {
			var l = t.lines[i];
			if (!l.accountName)
				l.accountName = $scope.currencies[l.account].name;
		}

		t.lines.push(newLine());

		$scope.lines = t.lines;
		$scope.updateTotalAmount();
		$scope.checkCurrencies();

		// problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
		// del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
		// comunque inutilizzabile
	}).
	then (undefined, function (error) {
		if (gdata.isError(error.data, gdata.E_already_modified)) {
			$location.path('/transaction/' + error.data[2] + '/d');
		} else {
			$scope.autocompletionDataError = error.data;
		}
	});
});

gassmanControllers.controller('TransactionCashExchange', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.tdate = new Date();
	$scope.tdesc = 'Accredito';
	$scope.totalAmount = 0.0;
	$scope.confirmDelete = false;
	$scope.currency = null;
	$scope.currencyError = false;
	$scope.currencies = {};
	$scope.autocompletionData = [];
	$scope.autocompletionDataError = null;
	$scope.csaId = null;
	$scope.tsaveOk = null;
	$scope.tsaveError = null;

	var newLine = function () {
		return {
			accountName: '',
			account: null,
			amount: '',
			notes: ''
		};
	};

	$scope.receiver = newLine();

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

	$scope.saveCashExchange = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.transId == 'new' ? null : $scope.transId,
			cc_type: 'x',
			currency: $scope.currency[0],
			lines: [],
			receiver: $scope.receiver.account,
			date: $scope.tdate,
			description: $scope.tdesc
		};

		for (var i in $scope.lines) {
			var l = $scope.lines[i];

			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		}

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.newTrans = function () {
		$scope.tdate = new Date();
		$scope.tdesc = 'Accredito';
		$scope.totalAmount = 0.0;
		$scope.confirmDelete = false;
		$scope.currency = null;
		$scope.tsaveOk = null;
		$scope.lines.push(newLine());
	};

	$scope.viewLastTrans = function () {
		$location.path('/transaction/' + $scope.savedTransId + '/x');
	};

	$scope.confirmCancelCashExchange = function () {
		$scope.confirmDelete = true;
		$timeout(function () { $scope.confirmDelete = false; }, 3200.0);
	};

	$scope.cancelCashExchange = function () {
		$scope.confirmDelete = false;

		var data = {
				transId: $scope.transId,
				cc_type: 't',
				currency: $scope.currency[0],
				lines: [],
				date: $scope.tdate,
				description: $scope.tdesc
			};

		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		for (var i in $scope.lines) {
			var l = $scope.lines[i];
			var a = l.account;

			if (!a)
				continue;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr.cur;
			} else if (!angular.equals($scope.currency, curr.cur)) {
				$scope.currency = null;
				$scope.currencyError = true;
				return;
			}
		}

		$scope.currencyError = false;
	};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.accountsNames($scope.csaId);
	}).then (function (r) {
		// trasforma data in autocompletionData

		$scope.currencies = accountAutocompletion.parse(r.data);

		$scope.autocompletionData = accountAutocompletion.compose($scope.currencies);

		if ($scope.transId == 'new')
			return {
				data: {
				transId: 'new',
				description: 'Accredito',
				date: new Date(),
				cc_type: 'x',
				currency: null,
				lines: []
			} };
		else
			return gdata.transactionForEdit($scope.csaId, $scope.transId);
	}).then(function (tdata) {
		var t = tdata.data;

		if (t.cc_type != 'x')
			throw "illegal type";

		$scope.transId = t.transId;
		$scope.tdesc = t.description;
		$scope.tdate = new Date(t.date);

		// caricata quindi rimuovo la riga negativa
		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);

			//console.log(x, typeof(x));
			if (x < 0) {
				t.lines.splice(i, 1);
				$scope.receiver.account = l.account;
			} else {
				l.amount = parseFloat(l.amount);
			}
		}

		for (var i in t.lines) {
			var l = t.lines[i];
			if (!l.accountName)
				l.accountName = $scope.currencies[l.account].name;
		}

		t.lines.push(newLine());

		var ra = $scope.currencies[$scope.receiver.account];
		$scope.receiver.accountName = ra ? ra.name : '';

		$scope.lines = t.lines;
		$scope.updateTotalAmount();
		$scope.checkCurrencies();

		// problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
		// del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
		// comunque inutilizzabile
	}).
	then (undefined, function (error) {
		if (gdata.isError(error.data, gdata.E_already_modified)) {
			$location.path('/transaction/' + error.data[2] + '/x');
		} else {
			$scope.autocompletionDataError = error.data;
		}
	});
});

gassmanControllers.controller('TransactionWithdrawal', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.tdate = new Date();
	$scope.tdesc = 'Prelievo';
	$scope.totalAmount = 0.0;
	$scope.confirmDelete = false;
	$scope.currency = null;
	$scope.currencyError = false;
	$scope.currencies = {};
	$scope.autocompletionData = [];
	$scope.autocompletionDataError = null;
	$scope.csaId = null;
	$scope.tsaveOk = null;
	$scope.tsaveError = null;

	var newLine = function () {
		return {
			accountName: '',
			account: null,
			amount: '',
			notes: ''
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

	$scope.saveWithdrawal = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.transId == 'new' ? null : $scope.transId,
			cc_type: 'w',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.tdate,
			description: $scope.tdesc
		};

		for (var i in $scope.lines) {
			var l = $scope.lines[i];

			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		}

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.newTrans = function () {
		$scope.tdate = new Date();
		$scope.tdesc = 'Prelievo';
		$scope.totalAmount = 0.0;
		$scope.confirmDelete = false;
		$scope.currency = null;
		$scope.tsaveOk = null;
		$scope.lines.push(newLine());
	};

	$scope.viewLastTrans = function () {
		$location.path('/transaction/' + $scope.savedTransId + '/w');
	};

	$scope.confirmCancelWithdrawal = function () {
		$scope.confirmDelete = true;
		$timeout(function () { $scope.confirmDelete = false; }, 3200.0);
	};

	$scope.cancelWithdrawal = function () {
		$scope.confirmDelete = false;

		var data = {
				transId: $scope.transId,
				cc_type: 't',
				currency: $scope.currency[0],
				lines: [],
				date: $scope.tdate,
				description: $scope.tdesc
			};

		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		for (var i in $scope.lines) {
			var l = $scope.lines[i];
			var a = l.account;

			if (!a)
				continue;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr.cur;
			} else if (!angular.equals($scope.currency, curr.cur)) {
				$scope.currency = null;
				$scope.currencyError = true;
				return;
			}
		}

		$scope.currencyError = false;
	};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.accountsNames($scope.csaId);
	}).then (function (r) {
		// trasforma data in autocompletionData

		$scope.currencies = accountAutocompletion.parse(r.data);

		$scope.autocompletionData = accountAutocompletion.compose($scope.currencies);

		if ($scope.transId == 'new')
			return {
				data: {
				transId: 'new',
				description: 'Prelievo',
				date: new Date(),
				cc_type: 'w',
				currency: null,
				lines: []
			} };
		else
			return gdata.transactionForEdit($scope.csaId, $scope.transId);
	}).then(function (tdata) {
		var t = tdata.data;

		if (t.cc_type != 'w')
			throw "illegal type";

		$scope.transId = t.transId;
		$scope.tdesc = t.description;
		$scope.tdate = new Date(t.date);

		// caricata quindi rimuovo la riga negativa
		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);

			//console.log(x, typeof(x));
			if (x > 0) {
				t.lines.splice(i, 1);
			} else {
				l.amount = - x;
			}
		}

		for (var i in t.lines) {
			var l = t.lines[i];
			if (!l.accountName)
				l.accountName = $scope.currencies[l.account].name;
		}

		t.lines.push(newLine());

		$scope.lines = t.lines;
		$scope.updateTotalAmount();
		$scope.checkCurrencies();

		// problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
		// del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
		// comunque inutilizzabile
	}).
	then (undefined, function (error) {
		if (gdata.isError(error.data, gdata.E_already_modified)) {
			$location.path('/transaction/' + error.data[2] + '/w');
		} else {
			$scope.autocompletionDataError = error.data;
		}
	});
});

gassmanControllers.controller('TransactionPayment', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.producers = [];
	$scope.expenses = [];
	//$scope.accounts = {};
	$scope.tdate = new Date();
	$scope.tdesc = 'Pagamento';
	$scope.totalAmount = 0.0;
	$scope.totalInvoice = 0.0;
	$scope.totalExpenses = 0.0;
	$scope.difference = 0.0;
	$scope.confirmDelete = false;
	$scope.currency = null;
	$scope.currencyError = false;
	$scope.currencies = {};
	$scope.autocompletionData = [];
	$scope.autocompletionExpenses = [];
	$scope.autocompletionDataError = null;
	$scope.csaId = null;
	$scope.tsaveOk = null;
	$scope.tsaveError = null;

	var autoCompileTotalInvoice = 2;

	var autoCompilingTotalInvoice = function () {
		if (
			$scope.producers.length < 3 &&
			($scope.producers.length == 1 || (!$scope.producers[1].accountName && !$scope.producers[1].amount)) &&
			$scope.producers[0].amount == $scope.totalInvoice &&
			$scope.expenses.length == 1 &&
			!$scope.expenses[0].desc && !$scope.expenses[0].amount
			)
			return 2;
		if (
			$scope.expenses.length < 3 &&
			($scope.expenses.length == 1 || (!$scope.expenses[1].desc && !$scope.expenses[1].amount)) &&
			$scope.expenses[0].amount == $scope.totalAmount - $scope.totalInvoice
			)
			return 1;
		return 0;
	};

	var newLine = function () {
		return {
			accountName: '',
			account: null,
			amount: '',
			notes: ''
		};
	};

	$scope.checkLine = function (e, ll) {
		if (e.account)
			ll.push(newLine());
	};

	$scope.checkExp = function (e, ll) {
		if (e.notes)
			ll.push(newLine());
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

		if (autoCompileTotalInvoice == 2) {
			$scope.producers[0].amount = $scope.totalAmount;

			$scope.updateTotalInvoice();
		} else if (autoCompileTotalInvoice == 1) {
			$scope.expenses[0].amount = $scope.totalAmount - $scope.totalInvoice;
		} else {
			$scope.difference = Math.abs($scope.totalAmount - $scope.totalInvoice - $scope.totalExpenses);
		}
	}

	$scope.updateTotalInvoice = function (f) {
		var ac = autoCompilingTotalInvoice();
		if (f !== undefined && ac < autoCompileTotalInvoice) {
			autoCompileTotalInvoice = ac;
		}

		//console.log('update total invoice', f);
		var t = 0.0;
		for (var i in $scope.producers) {
			var l = $scope.producers[i];
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		}

		$scope.totalInvoice = t;

		$scope.difference = Math.abs($scope.totalAmount - $scope.totalInvoice - $scope.totalExpenses);
	}

	$scope.updateTotalExpenses = function (f) {
		var ac = autoCompilingTotalInvoice();
		if (f !== undefined && ac < autoCompileTotalInvoice) {
			autoCompileTotalInvoice = ac;
		}

		//console.log('update total invoice', f);
		var t = 0.0;
		for (var i in $scope.expenses) {
			var l = $scope.expenses[i];
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		}

		$scope.totalExpenses = t;

		$scope.difference = Math.abs($scope.totalAmount - $scope.totalInvoice - $scope.totalExpenses);
	}

	$scope.savePayment = function () {
		if ($scope.$invalid ||
			$scope.currencyError ||
			$scope.difference > .01)
			return;

		var data = {
			transId: $scope.transId == 'new' ? null : $scope.transId,
			cc_type: 'p',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.tdate,
			description: $scope.tdesc
		};

		var f = -1;
		var cc = function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push({
						amount: l.amount * f,
						account: l.account,
						notes: l.notes
					});
				}
			}
		}

		angular.forEach($scope.lines, cc);
		f = +1;
		angular.forEach($scope.producers, cc);
		angular.forEach($scope.expenses, function (l) {
			// a differenza di clienti e produttori, qui non ho il conto:
			// lo inserisce il server in base a csa e currency
			if (l.amount > 0.0) {
				data.lines.push({
					amount: l.amount,
					notes: l.notes,
					account: null
				});
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.producers = [];
			$scope.expenses = [];
			//$scope.accounts = {};
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.newTrans = function () {
		$scope.tdate = new Date();
		$scope.tdesc = 'Pagamento';
		$scope.totalAmount = 0.0;
		$scope.totalInvoice = 0.0;
		$scope.totalExpenses = 0.0;
		$scope.confirmDelete = false;
		$scope.currency = null;
		$scope.tsaveOk = null;
		$scope.lines.push(newLine());
		$scope.producers.push(newLine());
		$scope.expenses.push(newLine());
	};

	$scope.viewLastTrans = function () {
		$location.path('/transaction/' + $scope.savedTransId + '/p');
	};

	$scope.confirmCancelPayment = function () {
		$scope.confirmDelete = true;
		$timeout(function () { $scope.confirmDelete = false; }, 3200.0);
	};

	$scope.cancelPayment = function () {
		$scope.confirmDelete = false;

		var data = {
				transId: $scope.transId,
				cc_type: 't',
				currency: $scope.currency[0],
				lines: [],
				date: $scope.tdate,
				description: $scope.tdesc
			};

		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			console.log(r);
			$scope.savedTransId = r.data;
			$scope.transId = 'new';
			$scope.lines = [];
			$scope.producers = [];
			$scope.expenses = [];
			//$scope.accounts = {};
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		var cc = function (l) {
			var a = l.account;

			if (!a)
				return;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr.cur;
			} else if (!angular.equals($scope.currency, curr.cur)) {
				throw 'err';
			}
		}

		try {
			angular.forEach($scope.lines, cc);
			angular.forEach($scope.producers, cc);

			$scope.currencyError = false;
		} catch (e) {
			$scope.currency = null;
			$scope.currencyError = true;
		}
	};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.accountsNames($scope.csaId);
	}).then (function (r) {
		// trasforma data in autocompletionData

		$scope.currencies = accountAutocompletion.parse(r.data);

		$scope.autocompletionData = accountAutocompletion.compose($scope.currencies);

		return gdata.expensesTags($scope.csaId);
	}).then(function (r) {
		var expensesAccounts = r.data.accounts;
		var expensesTags = r.data.tags;

		angular.forEach(expensesAccounts, function (account) {
			// 0:id, 1:gc_name, 3:currency_id
			$scope.autocompletionExpenses.push(account[1]);
		});

		angular.forEach(expensesTags, function (tag) {
			$scope.autocompletionExpenses.push(tag);
		});

		if ($scope.transId == 'new')
			return {
				data: {
				transId: 'new',
				description: 'Pagamento',
				date: new Date(),
				cc_type: 'p',
				currency: null,
				lines: []
			} };
		else
			return gdata.transactionForEdit($scope.csaId, $scope.transId);
	}).then(function (tdata) {
		var t = tdata.data;

		if (t.cc_type != 'p')
			throw "illegal type";

		$scope.transId = t.transId;
		$scope.tdesc = t.description;
		$scope.tdate = new Date(t.date);

		var clients = [];
		var producers = [];
		var expenses = [];

		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);
			var ac = $scope.currencies[l.account];

			//console.log(x, typeof(x));
			if (x < 0) {
				clients.push(l);
				l.amount = -x;
			} else if (ac && Object.keys(ac.people).length) {
				producers.push(l);
				l.amount = +x;
			} else {
				expenses.push(l);
				l.amount = +x;
				continue;
			}

			if (!l.accountName)
				l.accountName = $scope.currencies[l.account].name;
		}

		clients.push(newLine());
		producers.push(newLine());
		expenses.push(newLine());

		$scope.lines = clients;
		$scope.producers = producers;
		$scope.expenses = expenses;

		autoCompileTotalInvoice = t.transId != 'new' ? 0 : 2;

		$scope.updateTotalAmount();
		$scope.updateTotalInvoice();
		$scope.updateTotalExpenses()
		$scope.checkCurrencies();

		// problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
		// del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
		// comunque inutilizzabile
	}).
	then (undefined, function (error) {
		if (gdata.isError(error.data, gdata.E_already_modified)) {
			$location.path('/transaction/' + error.data[2] + '/p');
		} else {
			$scope.autocompletionDataError = error.data;
		}
	});
});

gassmanControllers.controller('TransactionsIndex', function($scope, $location, gdata) {
	$scope.transactions = null;
	$scope.transactionsError = null;
	$scope.queryFilter = '';
	$scope.queryOrder = 0;
	$scope.loadError = null;
	$scope.lastTransId = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = '';
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;

		reset();
		$scope.loadMore();
	};

	var reset = function () {
		$scope.transactions = [];
		$scope.transactionsError = null;
		start = 0;
		$scope.concluded = false;
	};

	gdata.selectedCsa().
	then (function (csaId) { $scope.csaId = csaId; $scope.loadMore(); }).
	then (undefined, function (error) { $scope.loadError = error.data; });

	$scope.loadMore = function () {
		if ($scope.concluded) return;

		gdata.transactionsLog($scope.csaId, lastQuery, lastQueryOrder, start, blockSize).
		then (function (r) {
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.transactions = $scope.transactions == null ? r.data : $scope.transactions.concat(r.data);
		}).
		then (undefined, function (error) {
			$scope.concluded = true;
			$scope.loadError = error.data[1];
			console.log('transactions log error: ', error.data);
		});
	};

	$scope.showTransaction = function (tl) {
		$location.path('/transaction/' + tl[3] + '/' + tl[7]);
	};
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

gassmanControllers.controller('PersonDetails', function($scope, $filter, $routeParams, $location, gdata) {
	$scope.csaId = null;
	$scope.personProfile = null;
	$scope.personProfileError = null;
	$scope.readOnly = true;
	$scope.editable = false;
	$scope.saveError = null;

	var master = null;
	var personId = $routeParams['personId'];
/*
	$scope.visibleAddress = function (c) {
		return c.kind !== 'I';
	};
*/
	$scope.addressKind = function (k) {
		return function (c) {
			return c.kind == k;
		}
	};
	$scope.hasAddressOfKind = function (k) {
		for (var i in $scope.personProfile.contacts) {
			if ($scope.personProfile.contacts[i].kind == k)
				return true;
		}
		return false;
	};

	$scope.visibleAccount = function (a) {
		return a.csa_id == $scope.csaId;
	};

	$scope.modify = function () {
		if ($scope.readOnly) {
			master = angular.copy($scope.personProfile);
			$scope.readOnly = false;
			$scope.saveError = null;
		}
	};

	$scope.isUnchanged = function () {
		return angular.equals($scope.personProfile, master);
	};

	$scope.save = function () {
		var f = $filter('filter');
		var cc = f($scope.personProfile.contacts, function (c) {
			return !!c.address;
		})

		$scope.personProfile.contacts = cc;

		gdata.saveProfile($scope.csaId, $scope.personProfile).
		then (function (r) {
			$scope.readOnly = true;
		}).
		then (undefined, function (error) {
			console.log('save error', error);
			$scope.saveError = error.data;
		});
	};

	$scope.cancel = function () {
		if (!$scope.readOnly) {
			$scope.readOnly = true;
			$scope.personProfile = master;
		}
	};

	$scope.addContact = function (k) {
		$scope.personProfile.contacts.push({
			address: '',
			kind: k,
			contact_type: '',
			id: -1,
			priority: 0,
			person_id: $scope.personProfile.profile.id
		});
	};

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/details');
	};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;
		return gdata.profile(csaId, personId);
	}).
	then (function (prof) {
		$scope.personProfile = prof;
	}).
	then (undefined, function (error) {
		$scope.personProfileError = error.data;
	});
});

/*
gassmanControllers.controller('ContactsController', function($scope, $filter, $location, gdata) {
	$scope.people = [];
	$scope.peopleError = null;
	$scope.queryFilter = '';
	$scope.queryOrder = 0;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = '';
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;

		reset();
		$scope.loadMore();
	};

	var reset = function () {
		$scope.people = [];
		$scope.peopleError = null;
		start = 0;
		$scope.concluded = false;
	};

	$scope.loadMore = function () {
		if ($scope.concluded) return;

		gdata.selectedCsa().
		then (function (csaId) { return gdata.peopleIndex(csaId, lastQuery, lastQueryOrder, start, blockSize); }).
		then(function (r) {
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.people = $scope.people.concat(r.data);
		}).
		then (undefined, function (error) {
			$scope.concluded = true;
			$scope.peopleError = error.data;
		});
	};

	$scope.showProfile = function (personId) {
		$location.path('/person/' + personId + '/details');
	};

	$scope.loadMore();
});
*/
