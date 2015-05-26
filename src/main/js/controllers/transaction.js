'use strict';

angular.module('GassmanApp.controllers.Transaction', [
	'GassmanApp.directives.RequiredIf',
	'GassmanApp.directives.GmUniqueEmail',
	'GassmanApp.directives.GmCurrency',
	'GassmanApp.directives.GmRequiredAccount',
    'gassmanServices',
    'ui.select'
])

.controller('Transaction', [
         '$scope', '$routeParams', '$location', '$timeout', 'gdata', 'accountAutocompletion',
function ($scope,   $routeParams,   $location,   $timeout,   gdata,   accountAutocompletion) {
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
					refs:[]
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
		$scope.updateTotalExpenses();
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
	};

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
	};

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
	};

    $scope.accountCurrency = function (a) {
        try {
            return $scope.currencies[a].cur[1];
        } catch (e) {
            return ' ';
        }
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

	$scope.focusElement = function (eid) {
		var e = angular.element(eid);
		$timeout(function () {
			e.focus();
		});
	};
/*
	$scope.focusAmount = function (type) {
		var e = angular.element('#' + type + this.$index)[0];
		$timeout(function () {
			e.focus();
		}, 1);
	};
*/
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
}])
;
