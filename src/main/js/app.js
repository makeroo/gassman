'use strict';

angular.module('gassmanApp', [
    'ui.router',
    'ngSanitize',

    'ui.bootstrap',

    'GassmanApp.services.Gstorage',

    'GassmanApp.controllers.CookieBanner',
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
    'GassmanApp.controllers.TransactionMembershipFee',
    'GassmanApp.controllers.ProjectController',
	'GassmanApp.controllers.AdminPeople'
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

    var appStarted = [
                 '$rootScope',
        function ($rootScope) {
            return $rootScope.gassman.appStarted;
        }
    ];
    var checkLoggedUser = [
                 '$rootScope', 'gdata', '$q',
        function ($rootScope,   gdata,   $q) {
            var d = $q.defer();

            $rootScope.gassman.appStarted.then(function () {
                if ($rootScope.gassman.loggedUser) {
                    d.resolve($rootScope.gassman.loggedUser);
                } else {
                    d.reject([gdata.error_codes.E_not_authenticated]);
                }
            });

            return d.promise;
        }
    ];
    var checkSelectedCsa = [
                 '$rootScope', 'gdata', '$q',
        function ($rootScope,   gdata,   $q) {
            var d = $q.defer();

            $rootScope.gassman.appStarted.then(function () {
                if ($rootScope.gassman.loggedUser) {
                    d.resolve($rootScope.gassman.selectedCsa);
                } else {
                    d.reject([gdata.error_codes.E_no_csa_found]);
                }
            });

            return d.promise;
        }
    ];
    var checkUserLoading = [
                 '$rootScope', '$q',
        function ($rootScope,   $q) {
            return $q.when($rootScope.gassman.userLoading);
        }
    ];

    $stateProvider.
        state('root', {
            abstract: true,
            resolve: {
                appStarted: appStarted
            },
            templateUrl: 'template/master.html'
        }).
        state('root.csa', {
            url: '/csa/:csaId/detail',
            resolve: {
                userAuthenticated: checkLoggedUser
            },
            templateUrl: 'template/csa_detail.html',
            controller: 'CsaDetail'
        }).
        state('root.csa_admin', {
            url: '/csa/{csaId:[0-9]+}/admin',
            resolve: {
                userAuthenticated: checkLoggedUser
            },
            templateUrl: 'template/csa_admin.html',
            controller: 'CsaAdmin'
        }).
        state('root.person_detail', {
            url: '/person/:personId/detail',
            resolve: {
                userAuthenticated: checkLoggedUser,
                csaSelected: checkSelectedCsa
            },
            templateUrl: 'template/person_detail.html',
            controller: 'PersonDetail'
        }).
        state('root.self_detail', {
            url: '/account/self/detail',
            resolve: {
                userAuthenticated: checkLoggedUser,
                csaSelected: checkSelectedCsa
            },
            templateUrl: 'template/account_detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_detail', {
            url: '/account/:accountId/detail',
            resolve: {
                userAuthenticated: checkLoggedUser,
                csaSelected: checkSelectedCsa
            },
            templateUrl: 'template/account_detail.html',
            controller: 'AccountDetail'
        }).
        state('root.account_list', {
            url: '/accounts/index',
            resolve: {
                userAuthenticated: checkLoggedUser,
                csaSelected: checkSelectedCsa,
                userLoaded: checkUserLoading
            },
            templateUrl: 'template/accounts_index.html',
            controller: 'AccountsIndex'
        }).
        state('root.transaction_detail', {
            url: '/transaction/:transId',
            resolve: {
                userAuthenticated: checkLoggedUser,
                csaSelected: checkSelectedCsa
            },
            templateUrl: 'template/transaction.html',
            controller: 'Transaction'
        }).
        state('root.transaction_list', {
            url: '/transactions/index',
            resolve: {
                csaSelected: checkSelectedCsa
            },
            templateUrl: 'template/transactions_index.html',
            controller: 'TransactionsIndex'
        }).
        state('root.admin', {
            abstract: true,
            url: '/admin',
            template: '<div ui-view></div>'
        }).
        state('root.admin.people', {
            url: '/people',
            templateUrl: 'template/admin_people.html',
            controller: 'AdminPeople'
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
            templateUrl: 'template/project.html',
            controller: 'ProjectController'
        }).
        state('root.privacy', {
            url: '/privacy',
            templateUrl: 'template/privacy.html',
            controller: 'PrivacyController'
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
         '$rootScope', 'gdata', 'gstorage', '$state', '$q', '$cookies', '$timeout',
function ($rootScope,   gdata,   gstorage,   $state,   $q,   $cookies,   $timeout) {
    var appStartedDefer = $q.defer();

    $rootScope.gassman = {
        loggedUser: null,
        selectedCsa: null,
        selectedAccount: null,
        appStarted: appStartedDefer.promise,
        userLoading: false
    };

    var userLoading = null;

    $rootScope.$watch('gassman.selectedCsa', function (v) {

        if (userLoading == null) {
            userLoading = $q.defer();

            $rootScope.gassman.userLoading = userLoading.promise;
        }

        // quando cambia csa devo ricaricare il profilo perché
        // cambiano conti e permessi

        gdata.profileInfo(v)
        .then(function (r) {
            $rootScope.gassman.loggedUser = r.data;

            return gstorage.selectedCsa();
        })
        .then (function (csaId) {
            // solo la prima volta assegno diverso, le successive
            // invece riassegno lo stesso valore
            $rootScope.gassman.selectedCsa = csaId;

            if (csaId !== null) {
                $rootScope.gassman.selectedAccount = gdata.accountByCsa(csaId);
            }
        })
        .then(undefined, function (error) {
            // TODO: che fine fa loggedUser? e selectedCsa?
        })
        .finally(function () {
            appStartedDefer.resolve(true);
            if ($rootScope.gassman.selectedAccount != null || $rootScope.gassman.selectedCsa == null) {
                userLoading.resolve(false);

                userLoading = null;
            }
        });
    });

    $rootScope.logout = function () {
        $cookies.remove('user');
        $rootScope.gassman.loggedUser = null;
        $rootScope.gassman.selectedCsa = null;

        $timeout(function () {
            window.location.reload();
        }, 500);
    };

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
