'use strict';

angular.module('gassmanApp', [
    'ui.router',
    'ngSanitize',

    'GassmanApp.services.Gstorage',

    'GassmanApp.directives.WhenScrolled',

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
    $urlRouterProvider.otherwise('/not_found');

    var loggedUser = [
                 'gdata',
        function (gdata) {
            return gdata.profileInfo();
        }
    ];
    var csa = [
                 'gdata',
        function (gdata) {
            return gdata.selectedCsa();
        }
    ];

    $stateProvider.
        state('root', {
            abstract: true,
            templateUrl: 'template/master.html'
            //controller: 'MasterController'
        }).
        state('root.csa', {
            url: '/csa/:csaId/detail',
            resolve: {
                loggedUser: loggedUser
            },
            templateUrl: 'template/csa_detail.html',
            controller: 'CsaDetail'
        }).
        state('root.csa_admin', {
            url: '/csa/{csaId:[0-9]+}/admin',
            resolve: {
                loggedUser: loggedUser
            },
            templateUrl: 'template/csa_admin.html',
            controller: 'CsaAdmin'
        }).
        state('root.person_detail', {
            url: '/person/:personId/detail',
            resolve: {
                loggedUser: loggedUser,
                csa: csa
            },
            templateUrl: 'template/person_detail.html',
            controller: 'PersonDetail'
        }).
        state('root.self_detail', {
            url: '/account/self/detail',
            resolve: {
                loggedUser: loggedUser,
                csa: csa
            },
            templateUrl: 'template/account_detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_detail', {
            url: '/account/:accountId/detail',
            resolve: {
                loggedUser: loggedUser,
                csa: csa
            },
            templateUrl: 'template/account_detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_list', {
            url: '/accounts/index',
            templateUrl: 'template/accounts_index.html',
            controller: 'AccountsIndex'
        }).
        state('root.transaction_detail', {
            url: '/transaction/:transId',
            templateUrl: 'template/transaction.html',
            controller: 'Transaction'
        }).
        state('root.transaction_list', {
            url: '/transactions/index',
            resolve: {
                csa: csa
            },
            templateUrl: 'template/transactions_index.html',
            controller: 'TransactionsIndex'
        }).
        state('root.help', {
            url: '/help',
            templateUrl: 'template/help.html'
        }).
        state('root.faq', {
            url: '/faq',
            templateUrl: 'template/faq.html'
        }).
        state('root.project', {
            url: '/project',
            templateUrl: 'template/project.html'
        }).
        state('root.not_found', {
            url: '/not_found',
            templateUrl: 'template/not_found.html',

            do_not_save: true
        }).
        state('root.start', {
            url: '/',
            templateUrl: 'template/home.html',
            controller: 'HomeSelectorController',

            do_not_save: true
        }).
        state('root.start2', {
            url: '',
            templateUrl: 'template/home.html',
            controller: 'HomeSelectorController',

            do_not_save: true
        }).
        state('root.login', {
            url: '/login',
            templateUrl: 'template/login.html',

            do_not_save: true
        }).
        state('root.error', {
            templateUrl: 'template/error.html',
            params: { 'error': null },

            do_not_save: true
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
         '$rootScope', 'gdata', 'gstorage', '$state',
function ($rootScope,   gdata,   gstorage,   $state) {
    $rootScope.$on('$stateChangeError', function (event, toState, toParams, fromState, fromParams, error) {
        if (error && error[0] == gdata.error_codes.E_not_authenticated) {
            if (!toState.do_not_save) {
                var req = window.location.hash.slice(1); // hash returns #/... but $location.path requires /...

                gstorage.saveRequestedUrl(req);
            }

            $state.go('root.login');
        } else {
            console.log('azz', arguments);

            $state.go('root.error', { error: error })
        }
    });

    $rootScope.appLoaded = true;
}])

;
