'use strict';

var gassmanControllers = angular.module('gassmanControllers', [
    'gassmanServices',
    'gassmanDirectives',
    'Mac',
	'ngStorage',
    ]);

function joinSkippingEmpties () {
	var sep = arguments[0];
	var r = '';
	for (var i = 1; i < arguments.length; ++i) {
		var x = arguments[i];
		if (typeof(x) != 'string' || x.length == 0)
			continue;
		if (r.length > 0)
			r += sep;
		r += x;
	}
	return r;
}

gassmanControllers.controller('NotFoundController', function() {
});

gassmanControllers.controller('HomeSelectorController', function($scope, $location, gdata) {
	$scope.error = null;

	gdata.profileInfo().
	then (function (profile) {
		$scope.profile = profile;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		if (typeof(csaId) == 'string' && csaId)
			$location.path('/csa/' + csaId + "/detail");
		else
			$location.path('/person/' + $scope.profile.logged_user.id + '/detail');
	}).
	then (undefined, function (error) {
		$scope.error = error;
	});
});


gassmanControllers.controller('MenuController', function($scope, $filter, gdata) {
	$scope.profile = null;
	$scope.profileError = null;
	$scope.functions = [];
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
	};

	$scope.$on('AmountsChanged', function () {
		reloadAmounts();
	});

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;

		angular.forEach(gassmanApp.functions, function (f) {
			if (('p' in f && pData.permissions.indexOf(f.p) == -1) ||
				('e' in f && !f.e(pData.permissions))
				)
				return;

			$scope.functions.push(f);
		});

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;
		return gdata.csaInfo(csaId);
	}).
	then (function (r) {
		$scope.csa = r.data;
		return gdata.accountByCsa($scope.csaId);
	}).
	then (function (accId) {
		$scope.accountId = accId;
		reloadAmounts();
	}).
	then (undefined, function (error) {
		$scope.profileError = error;
	});
});

gassmanControllers.controller('AccountDetail', function($scope, $filter, $routeParams, $location, gdata) {
	$scope.movements = [];
	$scope.movementsError = null;
	$scope.accountOwner = null;
	$scope.accountDesc = null;
	$scope.accountOwnerError = null;
	$scope.amount = null;
	$scope.viewableContacts = false;
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
			if (r.data.people)
				$scope.accountOwner = r.data.people;
			else
				$scope.accountDesc = r.data.desc;
		}).
		then (undefined, function (error) {
			$scope.accountOwnerError = error.data;
		});
	};

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;
		$scope.viewableContacts = $scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) != -1;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;

		return accId || gdata.accountByCsa(csaId);
	}).
	then (function (accId) {
		showOwner(accId);
		$scope.loadMore();

		return gdata.accountAmount(accId);
	}).
	then (function (r) {
		$scope.amount = r.data;
	}).
	then (undefined, function (error) {
		$scope.accountOwnerError = error.data;
	});

	$scope.showTransaction = function (mov) {
		$location.path('/transaction/' + mov[4]);
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
			console.log('AccountDetail: movements error:', error.data)
			$scope.showErrorMessage = false;
			$scope.movementsError = error.data;
			//console.log('error', data, status, headers, config);
		});
	};
});

gassmanControllers.controller('AccountsIndex', function($scope, $filter, $location, $localStorage, gdata) {
	$scope.accounts = [];
	$scope.accountsError = null;
	$scope.queryFilter = $localStorage.accountIndex_queryFilter || '';
	$scope.queryOrder = 0;
	$scope.profile = null;
	$scope.profileError = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = $scope.queryFilter;
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;
		$localStorage.accountIndex_queryFilter = $scope.queryFilter;

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
			$location.path('/account/' + accountId + '/detail');
		} else {
			$location.path('/person/' + personId + '/detail');
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

gassmanControllers.controller('Transaction', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
	var transId = $routeParams['transId'];
	var trans = {};

	$scope.trans = trans;

	if (gassmanApp.isPk(transId)) {
		trans.transId = transId;
		trans.cc_type = null;
	} else if (gassmanApp.isValidTransactionType(transId)) {
		trans.transId = 'new';
		trans.cc_type = transId;
	} else {
		// TODO: lanciare 404...
		// ovvero impostare le variabili sotto affinché
		// il template mostri errore
		throw 'illegal url';
	}

	$scope.modified_by = null;
	$scope.modifies = null;
	$scope.log_date = null;
	$scope.operator = null;
	$scope.totalAmount = null;
	$scope.totalInvoice = null;
	$scope.totalExpenses = null;
	$scope.difference = null;
	$scope.confirmDelete = false;
	$scope.currency = null;
	$scope.currencyError = null;
	$scope.currencies = {};
	$scope.autocompletionData = [];
	$scope.autocompletionExpenses = [];
	$scope.autocompletionDataError = null;
	$scope.csaId = null;
	$scope.tsaveOk = null;
	$scope.tsaveError = null;
	$scope.readonly = true;
	$scope.canEdit = false;
	$scope.viewableContacts = false;

	var autoCompileTotalInvoice = 2;

	var autoCompilingTotalInvoice = function () {
		if (
			$scope.trans.producers.length < 3 &&
			($scope.trans.producers.length == 1 || (!$scope.trans.producers[1].accountName && !$scope.trans.producers[1].amount)) &&
			$scope.trans.producers[0].amount == $scope.totalInvoice &&
			$scope.trans.expenses.length == 1 &&
			!$scope.trans.expenses[0].desc && !$scope.trans.expenses[0].amount
			)
			return 2;
		if (
			$scope.trans.expenses.length < 3 &&
			($scope.trans.expenses.length == 1 || (!$scope.trans.expenses[1].desc && !$scope.trans.expenses[1].amount)) &&
			$scope.trans.expenses[0].amount == $scope.totalAmount - $scope.totalInvoice
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

	var setupTransaction = function (tdata) {
		var t = tdata.data;
		//var trans = $scope.trans; // è nella chiusura
		var clients = [];
		var producers = [];
		var expenses = [];

		if (trans.cc_type == null)
			trans.cc_type = t.cc_type;
		else if (t.cc_type != trans.cc_type)
			// TODO: che senso ha lanciare eccezione?
			// ovvero impostare le variabili sotto affinché
			// il template mostri errore
			throw "illegal transaction type";

		$scope.canEdit = gassmanApp.isTransactionTypeEditableByUser(trans.cc_type, $scope.profile);
		$scope.readonly = t.transId != 'new';

		if (!$scope.canEdit && !$scope.readonly) {
			// TODO: gestire l'errore
			throw "permission denied";
		}

		trans.transId = t.transId;
		trans.tdesc = t.description;
		trans.tdate = new Date(t.date);
		trans.clients = clients;
		trans.producers = producers;
		trans.expenses = expenses;
		$scope.modified_by = t.modified_by;
		$scope.modifies = t.modifies;
		$scope.log_date = t.log_date;
		$scope.operator = t.operator;

		for (var i in t.lines) {
			var l = t.lines[i];
			// il filtro currency digerisce anche le stringhe
			// mentre input="number" no, devo prima convertire in float
			// i Decimal su db vengono convertiti in json in stringa
			var x = parseFloat(l.amount);
			var owners = t.people[l.account]; //$scope.currencies[l.account];

			//console.log(x, typeof(x));
			if (owners && owners.length) {
				if (x < 0) {
					clients.push(l);
					l.amount = -x;
				} else {
					producers.push(l);
					l.amount = +x;
				}

				if (!l.accountName) {
					var ac = $scope.currencies[l.account];

					if (ac) {
						l.accountName = ac.name;
						l.readonly = false;
					} else {
						l.readonly = true;
					}
				}

				if (!l.accountNames) {
					var pp = [];

					angular.forEach(owners, function (o) {
						var person = $scope.accountPeopleIndex[o];
						pp.push({
							pid: person.profile.id,
							name: joinSkippingEmpties(' ', person.profile.first_name, person.profile.middle_name, person.profile.last_name)
						});
					});

					l.accountNames = pp;
					//l.accountNames = $scope.currencies[l.account].people;
				}
			} else if (t.kitty.indexOf(l.account) != -1) {
				if (x < 0) {
					clients.push(l);
					l.amount = -x;
				} else {
					producers.push(l);
					l.amount = +x;
				}


				if (!l.accountName) {
					l.accountName = 'CASSA COMUNE'; // FIXME: i18n
					l.readonly = false;
				}

				l.accountNames = [{
					//pid: null,
					name: 'CASSA COMUNE', // FIXME: i18n
					refs:[],
				}];
			} else {
				expenses.push(l);
				l.amount = +x;
			}
		}

		clients.push(newLine());
		producers.push(newLine());
		expenses.push(newLine());

		autoCompileTotalInvoice = $scope.trans.cc_type != 'p' || t.transId != 'new' ? 0 : 2;

		$scope.updateTotalAmount();
		$scope.updateTotalInvoice();
		$scope.updateTotalExpenses()
		$scope.checkCurrencies();
		$scope.autocompletionDataError = null;

		// problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
		// del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
		// comunque inutilizzabile
	};

	$scope.updateTotalAmount = function () {
		var t = 0.0;

		angular.forEach($scope.trans.clients, function (l) {
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		});

		$scope.totalAmount = t;

		if (autoCompileTotalInvoice == 2) {
			$scope.trans.producers[0].amount = $scope.totalAmount;

			$scope.updateTotalInvoice();
		} else if (autoCompileTotalInvoice == 1) {
			$scope.trans.expenses[0].amount = $scope.totalAmount - $scope.totalInvoice;
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

		angular.forEach($scope.trans.producers, function (l) {
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		});

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

		angular.forEach($scope.trans.expenses, function (l) {
			var a = parseFloat(l.amount);
			if (!isNaN(a))
				t += a;
		});

		$scope.totalExpenses = t;

		$scope.difference = Math.abs($scope.totalAmount - $scope.totalInvoice - $scope.totalExpenses);
	}

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
		};

		try {
			angular.forEach($scope.trans.clients, cc);
			angular.forEach($scope.trans.producers, cc);

			$scope.currencyError = false;
		} catch (e) {
			$scope.currency = null;
			$scope.currencyError = true;
		}
	};

	$scope.confirmDeleteTransaction = function () {
		$scope.confirmDelete = true;
		$timeout(function () { $scope.confirmDelete = false; }, 3200.0);
	};

	$scope.deleteTransaction = function () {
		$scope.confirmDelete = false;

		var data = {
				transId: $scope.trans.transId,
				cc_type: 't',
				currency: $scope.currency[0],
				lines: [],
				date: $scope.trans.tdate,
				description: $scope.trans.tdesc
			};

		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('Transaction: transactionSave/delete result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};

	$scope.addLine = function (where) {
		where.push(newLine());
	};
/*
	$scope.newTrans = function (tt, desc) {
		$scope.transId = 'new';
		$scope.cc_type = tt;
		$scope.trans = {
			tdate: new Date(),
			tdesc: desc,
			clients: [ newLine() ],
			producers: [ newLine() ],
			expenses: [ newLine() ],
		};
		$scope.totalAmount = 0.0;
		$scope.totalInvoice = 0.0;
		$scope.totalExpenses = 0.0;
		$scope.confirmDelete = false;
		$scope.currency = null;
		$scope.tsaveOk = null;
	};
*/
	$scope.filledLine = function (line) {
		return line.account != null;
	};

	$scope.modifyTransaction = function () {
		$scope.readonly = false;
	};

	$scope.reloadForm = function () {
		gdata.transactionForEdit($scope.csaId, $scope.trans.transId).
		then(setupTransaction).
		then(undefined, function (error) {
			$scope.autocompletionDataError = error.data;
		});
	};

	$scope.focusAmount = function (type) {
		var e = angular.element('#' + type + this.$index)[0];
		$timeout(function () {
			e.focus();
		}, 1);
	};

	$scope.showTransaction = function (tid) {
		$location.path('/transaction/' + tid);
	};

	var firstTransResp = null;

	gdata.profileInfo().
	then (function (profile) {
		$scope.profile = profile;
		$scope.isTransactionEditor = gassmanApp.canEditTransactions($scope.profile);
		$scope.viewableContacts = $scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) != -1;
		$scope.viewableContactsOrAccounts = $scope.viewableContacts || $scope.profile.permissions.indexOf(gassmanApp.P_canCheckAccounts) != -1;

		return gdata.selectedCsa();
	}).then (function (csaId) {
		$scope.csaId = csaId;

		if ($scope.isTransactionEditor)
			return gdata.accountsNames($scope.csaId);
		else
			return null;
	}).then (function (r) {
		// trasforma data in autocompletionData

		if (r) {
			$scope.currencies = accountAutocompletion.parse(r.data);

			$scope.autocompletionData = accountAutocompletion.compose($scope.currencies);
		} else {
			$scope.currencies = [ ];
			$scope.autocompletionData = { };
		}

		if ($scope.isTransactionEditor)
			return gdata.expensesTags($scope.csaId);
		else
			return null;
	}).then(function (r) {
		if (r) {
			var expensesAccounts = r.data.accounts;
			var expensesTags = r.data.tags;

			angular.forEach(expensesAccounts, function (account) {
				// 0:id, 1:gc_name, 3:currency_id
				$scope.autocompletionExpenses.push(account[1]);
			});

			angular.forEach(expensesTags, function (tag) {
				$scope.autocompletionExpenses.push(tag);
			});
		} else {
			$scope.autocompletionExpenses = [ ];
		}

		if ($scope.trans.transId == 'new')
			return {
				data: {
					transId: 'new',
					description: '',
					date: new Date(),
					cc_type: $scope.trans.cc_type,
					currency: null,
					lines: [],
					modified_by: null,
					modifies: null
					},
				people: {}
				};
		else
			return gdata.transactionForEdit($scope.csaId, $scope.trans.transId);
	}).then(function (r) {
		firstTransResp = r;

		var x = [];
		angular.forEach(r.data.people, function (pp) {
			angular.forEach(pp, function(p) {
				if (x.indexOf(p) == -1)
					x.push(p);
			});
		});

		return gdata.peopleProfiles($scope.csaId, x);
	}).then(function (r) {
		$scope.accountPeopleIndex = r.data;
		return firstTransResp;
	}).then(setupTransaction).
	then (undefined, function (error) {
		$scope.autocompletionDataError = error.data;
	});
});

gassmanControllers.controller('TransactionDeposit', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {

	$scope.saveDeposit = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'd',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.producers, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionDeposit: save result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
});

gassmanControllers.controller('TransactionCashExchange', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {

	$scope.saveCashExchange = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'x',
			currency: $scope.currency[0],
			lines: [],
			receiver: $scope.trans.clients[0].account,
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.producers, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionCashExchange: save result:', r);

			$scope.showTransaction(r.data);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
});

gassmanControllers.controller('TransactionWithdrawal', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {

	$scope.saveWithdrawal = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'w',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.clients, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionWithdrawal: save result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
});

gassmanControllers.controller('TransactionPayment', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {

	$scope.savePayment = function () {
		if ($scope.$invalid ||
			$scope.currencyError ||
			$scope.difference > .01)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'p',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
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
		};

		angular.forEach($scope.trans.clients, cc);
		f = +1;
		angular.forEach($scope.trans.producers, cc);
		angular.forEach($scope.trans.expenses, function (l) {
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
			//console.log('TransactionPayment: save result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.producers = [];
			//$scope.expenses = [];
			//$scope.accounts = {};
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
});

gassmanControllers.controller('TransactionGeneric', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
});

gassmanControllers.controller('TransactionTrashed', function($scope, $routeParams, $location, $timeout, gdata, accountAutocompletion) {
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
			console.log('TransactionIndex: transactionsLog error:', error.data);
		});
	};

	$scope.showTransaction = function (tl) {
		$location.path('/transaction/' + tl[3]);
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

gassmanControllers.controller('PersonDetail', function($scope, $filter, $routeParams, $location, gdata, $q) {
	$scope.csaId = null;
	$scope.personProfile = null;
	$scope.personProfileError = null;
	$scope.readOnly = true;
	$scope.editable = false;
	$scope.saveError = null;
	$scope.membership_fee = null;

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
		if (!$scope.personProfile)
			return false;
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
			if ($scope.personProfile.membership_fee)
				$scope.membership_fee = $scope.personProfile.membership_fee.amount;
		}).
		then (undefined, function (error) {
			console.log('PersonDetail: saveProfile error:', error);
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
		$location.path('/account/' + accountId + '/detail');
	};

	gdata.profileInfo().
	then (function (p) {
		$scope.profile = p;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.profile(csaId, personId);
	}).
	then (function (prof) {
		$scope.personProfile = prof;
		$scope.editable = $scope.profile.permissions.indexOf(gassmanApp.P_canEditContacts) != -1 ||
			personId == $scope.profile.logged_user.id;

		var amounts = [];
		angular.forEach($scope.personProfile.accounts, function (a) {
			amounts.push(gdata.accountAmount(a.id));
		});

		return $q.all(amounts);
	}).
	then (function (amounts) {
		var l = amounts.length;

		for (var c = 0; c < l; ++c) {
			var acc = $scope.personProfile.accounts[c];
			var am = amounts[c];
			acc.amount = am.data[0];
			acc.csym = am.data[1];

			if (acc.to_date == null) {
				// nb: qui assumo una sola moneta per gas... FIXME
				$scope.membership_fee = acc.membership_fee;
				$scope.aka_csym = acc.csym;

				if ($scope.profile.permissions.indexOf(gassmanApp.P_canEditAnnualKittyAmount) != -1) {
					$scope.personProfile.membership_fee = {
						//account: acc.id,
						amount: parseFloat(acc.membership_fee),
					};
				}
			}
		}
	}).
	then (undefined, function (error) {
		$scope.personProfileError = error.data;
	});
});

gassmanControllers.controller('CsaDetail', function($scope, $filter, $location, $routeParams, gdata, $q) {
	var csaId = $routeParams['csaId'];

	$scope.profile = null;
	$scope.csa = null;
	$scope.loadError = null;
	$scope.openOrders = null;
	//$scope.openOrdersError = null;
	$scope.deliveringOrders = null;
	//$scope.deliveringOrdersError = null;
	$scope.draftOrders = null;
	$scope.movements = null;

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/detail');
	};

	$scope.showTransaction = function (mov) {
		$location.path('/transaction/' + mov[4]);
	};

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;

		return $q.all([ gdata.csaInfo(csaId),
		                gdata.accountByCsa(csaId),
		                ]);
	}).
	then (function (r) {
		$scope.csa = r[0].data;
		$scope.accId = r[1];

		// TODO: in realtà degli ordini CPY mi interessano solo le mie ordinazioni!!
		return $q.all([
				gdata.accountMovements($scope.accId, 0, 5),
				gdata.accountAmount($scope.csa.kitty.id),
				//gdata.accountMovements($scope.csa.kitty.id, 0, 5),
				]);
	}).
	then (function (rr) {
		$scope.movements = rr[0].data;
		$scope.csa.kitty.amount = rr[1].data;
		//$scope.csa.kitty.movements = rr[2].data;
	}).
	then (undefined, function (error) {
		$scope.loadError = error.data;
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
		$location.path('/person/' + personId + '/detail');
	};

	$scope.loadMore();
});
*/
