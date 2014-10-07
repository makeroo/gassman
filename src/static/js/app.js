'use strict';

var gassmanApp = angular.module('gassmanApp', [
	'ngRoute',
	'gassmanControllers',
	'gassmanServices',
	'gassmanDirectives',
	'gassmanFilters'
	]);

gassmanApp.P_membership = 1;
gassmanApp.P_canCheckAccounts = 2;
//gassmanApp.P_canAssignAccounts = 3;
gassmanApp.P_canEnterDeposit = 4;
gassmanApp.P_canEnterPayments = 5;
gassmanApp.P_canManageTransactions = 6;
gassmanApp.P_canEnterCashExchange = 7;
gassmanApp.P_canEnterWithdrawal = 8;
gassmanApp.P_canViewContacts = 9;
gassmanApp.P_canEditContacts = 10;

gassmanApp.functions = [
	//{ p:gassmanApp.P_membership, f:'#/account/detail', l:'Il tuo conto' },
	{ e:function (pp) {
		return pp.indexOf(gassmanApp.P_canCheckAccounts) != -1 ||
		       pp.indexOf(gassmanApp.P_canViewContacts) != -1;
		}, f:'#/accounts/index', l:'Membri del G.A.S.' },
	//{ v:P_canAssignAccounts, f:null },
	{ e: function (pp) { return gassmanApp.canEditTransactions(null, pp) }, l:'Movimentazione contante', 'class': "grouptitle" },
	{ p:gassmanApp.P_canEnterCashExchange, f:'#/transaction/x', l:'Scambio contante' },
	{ p:gassmanApp.P_canEnterPayments, f:'#/transaction/p', l:'Registra pagamenti' },
	{ p:gassmanApp.P_canEnterDeposit, f:'#/transaction/d', l:'Registra accrediti' },
	{ p:gassmanApp.P_canEnterWithdrawal, f:'#/transaction/w', l:'Registra prelievi' },
	{ e: function (pp) { return gassmanApp.canEditTransactions(null, pp); }, f:'#/transactions/index', l:' Movimenti inseriti' }
	//,
	//{ p:gassmanApp.P_canViewContacts, f:'#/contacts/index', l:'Rubrica' }
	];

/*
gassmanApp.filter('noFractionCurrency',
		  [ '$filter', '$locale',
		  function(filter, locale) {
			var currencyFilter = filter('currency');
			var formats = locale.NUMBER_FORMATS;
			return function(amount, currencySymbol) {
			  var value = currencyFilter(amount, currencySymbol);
			  var sep = value.indexOf(formats.DECIMAL_SEP);
			  if(amount >= 0) { 
				return value.substring(0, sep);
			  }
			  return value.substring(0, sep) + ')';
			};
		  } ]);
*/

gassmanApp.config([ '$routeProvider',
	function ($routeProvider) {
		$routeProvider.
		when('/person/:personId/detail', {
			templateUrl: 'static/partials/person-detail.html',
			controller: 'PersonDetail'
		}).
			when('/account/self/detail', {
				templateUrl: 'static/partials/account-detail.html',
				controller: 'AccountDetail'
			}).
			when('/account/:accountId/detail', {
				templateUrl: 'static/partials/account-detail.html',
				controller: 'AccountDetail'
			}).
			when('/accounts/index', {
				templateUrl: 'static/partials/accounts-index.html',
				controller: 'AccountsIndex'
			}).
			when('/transaction/:transId', {
				templateUrl: 'static/partials/transaction.html',
				controller: 'Transaction'
			}).
/*
			when('/transaction/:transId/d', {
				templateUrl: 'static/partials/transaction_deposit.html',
				controller: 'TransactionDeposit'
			}).
			when('/transaction/:transId/p', {
				templateUrl: 'static/partials/transaction_payment.html',
				controller: 'TransactionPayment'
			}).
			when('/transaction/:transId/x', {
				templateUrl: 'static/partials/transaction_cashexchange.html',
				controller: 'TransactionCashExchange'
			}).
			when('/transaction/:transId/w', {
				templateUrl: 'static/partials/transaction_withdrawal.html',
				controller: 'TransactionWithdrawal'
			}).
			when('/transaction/:transId/g', {
				templateUrl: 'static/partials/transaction_generic.html',
				controller: 'TransactionGeneric'
			}).
			when('/transaction/:transId/t', {
				templateUrl: 'static/partials/transaction_trashed.html',
				controller: 'TransactionTrashed'
			}).
*/
			when('/transactions/index', {
				templateUrl: 'static/partials/transactions_index.html',
				controller: 'TransactionsIndex'
			}).
			when('/help', {
				templateUrl: 'static/partials/help.html',
				controller: 'HelpController'
			}).
			when('/faq', {
				templateUrl: 'static/partials/faq.html',
				controller: 'FaqController'
			}).
			when('/project', {
				templateUrl: 'static/partials/project.html',
				controller: 'ProjectController'
			}).
			//when('/contacts/index', {
			//	templateUrl: 'static/partials/contacts_index.html',
			//	controller: 'ContactsController'
			//}).
			otherwise({
				redirectTo: '/account/self/detail'
			})
	}]);

// funzioni di utilità, da trasferire in un servizio...

gassmanApp.isPk = function (v) {
	try {
		var i = parseInt(v);

		return !isNaN(i);
	} catch (e) {
		return false;
	}
};

gassmanApp.transactionTypes = {
	g: true, // non editabile
	t: true, // vale il tipo della precedente
	p: gassmanApp.P_canEnterPayments,
	x: gassmanApp.P_canEnterCashExchange,
	d: gassmanApp.P_canEnterDeposit,
	w: gassmanApp.P_canEnterWithdrawal
};
gassmanApp.isValidTransactionType = function (v) {
	return !!gassmanApp.transactionTypes[v];
};
gassmanApp.isTransactionTypeEditableByUser = function (t, u) {
	var p = gassmanApp.transactionTypes[t];

	if (angular.isNumber(p))
		return u.permissions.indexOf(p) != -1;
	else
		return false;
};
gassmanApp.canEditTransactions = function (u, pp) {
	if (!pp)
		pp = u.permissions;
	return (
		pp.indexOf(gassmanApp.P_canEnterPayments) != -1 ||
		pp.indexOf(gassmanApp.P_canEnterCashExchange) != -1 ||
		pp.indexOf(gassmanApp.P_canEnterDeposit) != -1 ||
		pp.indexOf(gassmanApp.P_canEnterWithdrawal) != -1 ||
		pp.indexOf(gassmanApp.P_canManageTransactions) != -1
		);
};
