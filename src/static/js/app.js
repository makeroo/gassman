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

gassmanApp.functions = [
	{ p:gassmanApp.P_membership, f:'#/account/detail', l:'Il tuo conto' },
	{ p:gassmanApp.P_canCheckAccounts, f:'#/accounts/index', l:'Tutti i conti',
	  justAdded: function ($scope, gdata) {
		gdata.selectedCsa().
		then(function (csaId) { return gdata.totalAmount(csaId); }).
		then(function (r) {
			$scope.totalAmount = r.data;
		}).
		then (undefined, function (error) {
			$scope.totalAmountError = error;
		});
	  }},
	//{ v:P_canAssignAccounts, f:null },
	{ p:gassmanApp.P_canEnterCashExchange, f:'#/transaction/new/x', l:'Scambio contante' },
	{ p:gassmanApp.P_canEnterPayments, f:'#/transaction/new/p', l:'Registra pagamenti' },
	{ p:gassmanApp.P_canEnterDeposit, f:'#/transaction/new/d', l:'Registra accrediti' },
	{ p:gassmanApp.P_canEnterWithdrawal, f:'#/transaction/new/w', l:'Registra prelievi' },
	{ e:function (pp) {
		return pp.indexOf(gassmanApp.P_canEnterPayments) != -1 ||
		       pp.indexOf(gassmanApp.P_canEnterDeposit) != -1 ||
		       pp.indexOf(gassmanApp.P_canEnterCashExchange) != -1 ||
		       pp.indexOf(gassmanApp.P_canEnterWithdrawal) != -1 ||
		       pp.indexOf(gassmanApp.P_canManageTransactions) != -1
	  }, f:'#/transactions/index', l:' Movimenti inseriti' }
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
			when('/account/self/details', {
				templateUrl: 'static/partials/account-details.html',
				controller: 'AccountDetails'
			}).
			when('/account/:accountId/details', {
				templateUrl: 'static/partials/account-details.html',
				controller: 'AccountDetails'
			}).
			when('/accounts/index', {
				templateUrl: 'static/partials/accounts-index.html',
				controller: 'AccountsIndex'
			}).
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
			otherwise({
				redirectTo: '/account/self/details'
			})
	}]);
