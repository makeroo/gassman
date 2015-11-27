'use strict';

angular.module('gassmanApp', [
	'ui.router',
    'ngSanitize',

    'GassmanApp.directives.WhenScrolled',

    'GassmanApp.controllers.NotFoundController',
	'GassmanApp.controllers.FaqController',
    'GassmanApp.controllers.ProjectController',
	'GassmanApp.controllers.HelpController',
    'GassmanApp.controllers.HomeSelectorController',
    'GassmanApp.controllers.Navbar',
    'GassmanApp.controllers.CsaDetail',
	'GassmanApp.controllers.CsaAdmin',
    'GassmanApp.controllers.AccountsIndex',
    'GassmanApp.controllers.AccountDetail',
    'GassmanApp.controllers.PersonDetail',
    'GassmanApp.controllers.TransactionsIndex',
    'GassmanApp.controllers.Transaction',
    'GassmanApp.controllers.TransactionCashExchange',
    'GassmanApp.controllers.TransactionPayment',
    'GassmanApp.controllers.TransactionTrashed',
	'GassmanApp.controllers.TransactionMembershipFee'
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
         '$stateProvider', '$urlRouterProvider',
function ($stateProvider,   $urlRouterProvider) {
	$urlRouterProvider.otherwise('/notfound');

	$stateProvider.
        state('root', {
            abstract: true,
            templateUrl: 'template/master.html'
            //controller: 'MasterController'
        }).
        state('root.csa', {
            url: '/csa/:csaId/detail',
            templateUrl: 'template/csa-detail.html',
            controller: 'CsaDetail'
        }).
        state('root.csa_admin', {
            url: '/csa/{csaId:[0-9]+}/admin',
            templateUrl: 'template/csa-admin.html',
            controller: 'CsaAdmin'
        }).
        state('root.person_detail', {
            url: '/person/:personId/detail',
            templateUrl: 'template/person-detail.html',
            controller: 'PersonDetail'
        }).
        state('root.self_detail', {
            url: '/account/self/detail',
            templateUrl: 'template/account-detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_detail', {
            url: '/account/:accountId/detail',
            templateUrl: 'template/account-detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_list', {
            url: '/accounts/index',
            templateUrl: 'template/accounts-index.html',
            controller: 'AccountsIndex'
        }).
        state('root.transaction_detail', {
            url: '/transaction/:transId',
            templateUrl: 'template/transaction.html',
            controller: 'Transaction'
        }).
        state('root.transaction_list', {
            url: '/transactions/index',
            templateUrl: 'template/transactions_index.html',
            controller: 'TransactionsIndex'
        }).
        state('root.help', {
            url: '/help',
            templateUrl: 'template/help.html',
            controller: 'HelpController'
        }).
        state('root.faq', {
            url: '/faq',
            templateUrl: 'template/faq.html',
            controller: 'FaqController'
        }).
        state('root.project', {
            url: '/project',
            templateUrl: 'template/project.html',
            controller: 'ProjectController'
        }).
        state('root.not_found', {
            url: '/not_found',
            templateUrl: 'template/not_found.html',
            controller: 'NotFoundController'
        }).
        state('root.start', {
            url: '/',
            templateUrl: 'template/home.html',
            controller: 'HomeSelectorController'
        }).
        state('root.start2', {
            url: '',
            templateUrl: 'template/home.html',
            controller: 'HomeSelectorController'
        })
/*		.state('start', {
			url: '',
			views: {
				main: {
					templateUrl: 'template/start.html',
					controller: 'StartController'
				}
			}
		})*/
	;
}])

.run([
         '$rootScope',
function ($rootScope) {
    $rootScope.appLoaded = true;
}])

;
