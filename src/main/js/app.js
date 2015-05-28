'use strict';

angular.module('gassmanApp', [
	'ngRoute',
    'ngSanitize',
    'GassmanApp.directives.WhenScrolled',
    'GassmanApp.controllers.NotFoundController',
    'GassmanApp.controllers.HomeSelectorController',
    'GassmanApp.controllers.Navbar',
    'GassmanApp.controllers.CsaDetail',
    'GassmanApp.controllers.AccountsIndex',
    'GassmanApp.controllers.AccountDetail',
    'GassmanApp.controllers.PersonDetail',
    'GassmanApp.controllers.TransactionsIndex',
    'GassmanApp.controllers.Transaction',
    'GassmanApp.controllers.TransactionDeposit',
    'GassmanApp.controllers.TransactionCashExchange',
    'GassmanApp.controllers.TransactionWithdrawal',
    'GassmanApp.controllers.TransactionPayment',
    'GassmanApp.controllers.TransactionGeneric',
    'GassmanApp.controllers.TransactionTrashed'
	])

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

.config([
         '$routeProvider',
function ($routeProvider) {
	$routeProvider.
	when('/csa/:csaId/detail', {
		templateUrl: 'template/csa-detail.html',
		controller: 'CsaDetail'
	}).
	when('/person/:personId/detail', {
		templateUrl: 'template/person-detail.html',
		controller: 'PersonDetail'
	}).
	when('/account/self/detail', {
		templateUrl: 'template/account-detail.html',
		controller: 'AccountDetail'
	}).
	when('/account/:accountId/detail', {
		templateUrl: 'template/account-detail.html',
		controller: 'AccountDetail'
	}).
	when('/accounts/index', {
		templateUrl: 'template/accounts-index.html',
		controller: 'AccountsIndex'
	}).
	when('/transaction/:transId', {
		templateUrl: 'template/transaction.html',
		controller: 'Transaction'
	}).
	when('/transactions/index', {
		templateUrl: 'template/transactions_index.html',
		controller: 'TransactionsIndex'
	}).
	when('/help', {
		templateUrl: 'template/help.html',
		controller: 'HelpController'
	}).
	when('/faq', {
		templateUrl: 'template/faq.html',
		controller: 'FaqController'
	}).
	when('/project', {
		templateUrl: 'template/project.html',
		controller: 'ProjectController'
	}).
	when('/not_found', {
		templateUrl: 'template/not_found.html',
		controller: 'NotFoundController'
	}).
	when('/', {
		templateUrl: 'template/home.html',
		controller: 'HomeSelectorController'
	}).
	otherwise({
		redirectTo: '/not_found'
	})
}])
;

// funzioni di utilità, da trasferire in un servizio...
