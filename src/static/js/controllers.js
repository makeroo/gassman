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

gassmanControllers.controller('TransactionDeposit', function($scope, $routeParams, $location, $timeout, gdata) {
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
				cc_type: 'T',
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

	$scope.selectedAccount = function (l, o) {
		l.account = o.acc;
		l.accountName = o.name;

//		var curr = $scope.currencies[o.acc];
//		if (!$scope.currency)
//			$scope.currency = curr;
//		else if ($scope.currency != curr)
//			$scope.currencyError = true;
		$scope.checkCurrencies();
	}

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		for (var i in $scope.lines) {
			var l = $scope.lines[i];
			var a = l.account;

			if (!a)
				continue;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr;
			} else if (!angular.equals($scope.currency, curr)) {
				$scope.currency = null;
				$scope.currencyError = true;
				return;
			}
		}

		$scope.currencyError = false;
	};

	var ai = {};

	gdata.selectedCsa().
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.accountsNames($scope.csaId);
	}).then (function (r) {
		// trasforma data in autocompletionData
		var accountNames = r.data.accountNames;
		var accountPeople = r.data.accountPeople;
		var accountPeopleAddresses = r.data.accountPeopleAddresses;
		var people = {};
		for (var i in accountNames) {
			var o = accountNames[i];
			// o è un array gc_name, accId
			$scope.autocompletionData.push({ name: o[0], acc: o[1] });
			$scope.currencies[o[1]] = [ o[2], o[3] ];
			ai[o[1]] = o[0];
		}
		for (var i in accountPeople) {
			var o = accountPeople[i];
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + ' ' + (o[2] || '') + ' ' + (o[3] || '');
			n = n.trim();
			people[o[0]] = n;
			$scope.autocompletionData.push({ name: n, acc: o[4], p: o[0] });
			ai[o[4]] = n; // sovrascrivo, non mi interessa
		}
		for (var i in accountPeopleAddresses) {
			var o = accountPeopleAddresses[i];
			// o è un array 0:addr 1:pid 2:accId
			var n = o[0] + ' (' + people[o[1]] + ')';
			$scope.autocompletionData.push({ name: n, acc: o[2], p: o[1] });
			if (!ai[o[2]])
				ai[o[2]] = n; // questa volta non sovrascrivo
		}

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
		$scope.tdata = t.data;

		if (!t.lines.length) {
			t.lines.push(newLine());
		} else {
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
		}

		for (var i in t.lines) {
			var l = t.lines[i];
			if (!l.accountName)
				l.accountName = ai[l.account];
		}

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

gassmanControllers.controller('TransactionPayment', function($scope, $routeParams, $location, $timeout, gdata) {
	$scope.transId = $routeParams['transId'];
	$scope.lines = [];
	$scope.producers = [];
	$scope.expenses = [];
	$scope.accounts = {};
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
			$scope.accounts = {};
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
				cc_type: 'T',
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
			$scope.accounts = {};
			$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.selectedAccount = function (l, o) {
		l.account = o.acc;
		l.accountName = o.name;

//		var curr = $scope.currencies[o.acc];
//		if (!$scope.currency)
//			$scope.currency = curr;
//		else if ($scope.currency != curr)
//			$scope.currencyError = true;
		$scope.checkCurrencies();
	}

	$scope.checkCurrencies = function () {
		$scope.currency = null;

		var cc = function (l) {
			var a = l.account;

			if (!a)
				return;

			var curr = $scope.currencies[a];

			if (!$scope.currency) {
				$scope.currency = curr;
			} else if (!angular.equals($scope.currency, curr)) {
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
		var accountNames = r.data.accountNames;
		var accountPeople = r.data.accountPeople;
		var accountPeopleAddresses = r.data.accountPeopleAddresses;
		var people = {};
		for (var i in accountNames) {
			var o = accountNames[i];
			// o è un array gc_name, accId
			$scope.autocompletionData.push({ name: o[0], acc: o[1] });
			$scope.currencies[o[1]] = [ o[2], o[3] ];
			$scope.accounts[o[1]] = o[0];
		}
		for (var i in accountPeople) {
			var o = accountPeople[i];
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + ' ' + (o[2] || '') + ' ' + (o[3] || '');
			n = n.trim();
			people[o[0]] = n;
			$scope.autocompletionData.push({ name: n, acc: o[4], p: o[0] });
			$scope.accounts[o[4]] = n; // sovrascrivo, non mi interessa
		}
		for (var i in accountPeopleAddresses) {
			var o = accountPeopleAddresses[i];
			// o è un array 0:addr 1:pid 2:accId
			var n = o[0] + ' (' + people[o[1]] + ')';
			$scope.autocompletionData.push({ name: n, acc: o[2], p: o[1] });
			if (!$scope.accounts[o[2]])
				$scope.accounts[o[2]] = n; // questa volta non sovrascrivo
		}
		return gdata.expensesTags($scope.csaId);
	}).then(function (r) {
		var expensesAccounts = r.data.accounts;
		var expensesTags = r.data.tags;

		angular.forEach(expensesAccounts, function (account) {
			// 0:id, 1:gc_name, 2:gc_id, 3:gc_parent, 4:currency_id
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
		$scope.tdata = t.data;

		var clients = [];
		var producers = [];
		var expenses = [];

		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);

			//console.log(x, typeof(x));
			if (x < 0) {
				clients.push(l);
				l.amount = -x;
			} else if (l.account in $scope.accounts){
				expenses.push(l);
			} else {
				producers.push(l);
				//l.amount = x;
			}

			if (!l.accountName)
				l.accountName = $scope.accounts[l.account];
		}

//		if (!clients.length)
			clients.push(newLine());
//		if (!producers.length)
			producers.push(newLine());
//		if (!expenses.length)
			expenses.push(newLine());

		$scope.lines = clients;
		$scope.producers = producers;
		$scope.expenses = expenses;
		$scope.updateTotalAmount();
		$scope.updateTotalInvoice();
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
	$scope.loadError = null;
	$scope.lastTransId = null;

	var concluded = false;
	var start = 0;
	var blockSize = 25;

	gdata.selectedCsa().
	then (function (csaId) { $scope.csaId = csaId; $scope.loadMore(); }).
	then (undefined, function (error) { $scope.loadError = error.data; });

	$scope.loadMore = function () {
		if (concluded) return;

		gdata.transactionsLog($scope.csaId, start, blockSize).
		then (function (r) {
			concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.transactions = $scope.transactions == null ? r.data : $scope.transactions.concat(r.data);
		}).
		then (undefined, function (error) {
			concluded = true;
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
