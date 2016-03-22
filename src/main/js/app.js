'use strict';

angular.module('gassmanApp', [
    'ui.router',
    'ngSanitize',

    'ui.bootstrap',

    'GassmanApp.services.Gstorage',

    'GassmanApp.controllers.CookieBanner',
    'GassmanApp.controllers.HomeSelectorController',
    'GassmanApp.controllers.Navbar',
    'GassmanApp.controllers.CsaBase',
    'GassmanApp.controllers.CsaDetail',
    'GassmanApp.controllers.CsaAdmin',
    'GassmanApp.controllers.CsaShifts',
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
            return $rootScope.gassman.appStarted.then(function () {
                return $rootScope.gassman.userLoading;
            }).then(function () {
                if ($rootScope.gassman.loggedUser) {
                    return $rootScope.gassman.loggedUser;
                } else {
                    throw [gdata.error_codes.E_not_authenticated];
                }
            });
        }
    ];
    var checkUserUserPermissions = function () {
        var permissions = arguments;

        // TODO: creare un servizio aaa con tutte le utility function tipo questa
        function hasAll (user, perms) {
            if (!user || !user.permissions)
                return false;

            for (var c = perms.length; --c >= 0; ) {
                if (user.permissions.indexOf(perms[c]) == -1) {
                    return false;
                }
            }

            return true;
        }

        return [
                     '$rootScope', 'gdata', '$q',
            function ($rootScope,   gdata,   $q) {
                return $rootScope.gassman.appStarted.then(function () {
                    return $rootScope.gassman.userLoading;
                }).then(function () {
                    if (hasAll($rootScope.gassman.loggedUser, permissions)) {
                        return $rootScope.gassman.loggedUser;
                    } else {
                        throw [gdata.error_codes.E_not_authenticated];
                    }
                });
            }
        ];
    };
    var checkSelectedCsa = [
                 '$rootScope', 'gdata', '$q',
        function ($rootScope,   gdata,   $q) {
            return $rootScope.gassman.appStarted.then(function () {
                if ($rootScope.gassman.loggedUser) {
                    return $rootScope.gassman.selectedCsa;
                } else {
                    throw [gdata.error_codes.E_not_authenticated];
                }
            });
        }
    ];
    var checkUserLoading = [
                 '$rootScope', '$q',
        function ($rootScope,   $q) {
            return $q.when($rootScope.gassman.userLoading);
        }
    ];
    var checkCsaLoading = [
                 '$rootScope', '$q',
        function ($rootScope,   $q) {
            return $q.when($rootScope.gassman.csaLoading);
        }
    ];

    $stateProvider
    .state('root', {
        abstract: true,
        resolve: {
            appStarted: appStarted
        },
        templateUrl: 'template/master.html'
    })
    .state('root.csa', {
        abstract: true,
        url: '/csa/{csaId:[0-9]+}',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa,
            csaLoaded: checkCsaLoading
        },
        template: '<div ui-view></div>',
        controller: 'CsaBase'
    })
    .state('root.csa.detail', {
        url: '/detail',
        templateUrl: 'template/csa_detail.html',
        controller: 'CsaDetail'
    })
    .state('root.csa.admin', {
        url: '/admin',
        resolve: {
            userAuthenticated: checkUserUserPermissions(13/*TODO:gdata.permissions.P_csaEditor*/),
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/csa_admin.html',
        controller: 'CsaAdmin'
    })
    .state('root.csa.shifts', {
        url: '/csa/{csaId:[0-9]+}/shifts',
        resolve: {
            userAuthenticated: checkUserUserPermissions(15/*TODO:gdata.permissions.P_canManageShifts*/),
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/csa_shifts.html',
        controller: 'CsaShifts'
    })
    .state('root.person_detail', {
        url: '/person/:personId/detail',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/person_detail.html',
        controller: 'PersonDetail'
    })
    .state('root.self_detail', {
        url: '/account/self/detail',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/account_detail.html',
        controller: 'AccountDetail'
    })
    .state('root.account_detail', {
        url: '/account/:accountId/detail',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/account_detail.html',
        controller: 'AccountDetail'
    })
    .state('root.account_list', {
        url: '/accounts/index',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa,
            userLoaded: checkUserLoading
        },
        templateUrl: 'template/accounts_index.html',
        controller: 'AccountsIndex'
    })
    .state('root.transaction_detail', {
        url: '/transaction/:transId',
        resolve: {
            userAuthenticated: checkLoggedUser,
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/transaction.html',
        controller: 'Transaction'
    })
    .state('root.transaction_list', {
        url: '/transactions/index',
        resolve: {
            csaSelected: checkSelectedCsa
        },
        templateUrl: 'template/transactions_index.html',
        controller: 'TransactionsIndex'
    })
    .state('root.admin', {
        abstract: true,
        url: '/admin',
        template: '<div ui-view></div>'
    })
    .state('root.admin.people', {
        url: '/people',
        resolve: {
            userAuthenticated: checkUserUserPermissions(3/*TODO:gdata.permissions.P_canAdminPeople*/)
        },
        templateUrl: 'template/admin_people.html',
        controller: 'AdminPeople'
    })
    .state('root.help', {
        url: '/help',
        templateUrl: 'template/help.html'
    })
    .state('root.faq', {
        url: '/faq',
        templateUrl: 'template/faq.html'
    })
    .state('root.project', {
        url: '/project',
        templateUrl: 'template/project.html',
        controller: 'ProjectController'
    })
    .state('root.privacy', {
        url: '/privacy',
        templateUrl: 'template/privacy.html'
    })
    .state('root.not_found', {
        url: '/not_found',
        templateUrl: 'template/not_found.html',

        do_not_save: true
    })
    .state('root.start', {
        url: '/',
        templateUrl: 'template/home.html',
        controller: 'HomeSelectorController',

        do_not_save: true
    })
    .state('root.start2', {
        url: '',
        templateUrl: 'template/home.html',
        controller: 'HomeSelectorController',

        do_not_save: true
    })
    .state('root.login', {
        url: '/login',
        templateUrl: 'template/login.html',

        do_not_save: true
    })
    .state('root.error', {
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
    $rootScope.addressKind = function (k) {
        return function (c) {
            return c.kind == k;
        }
    };

    var appStartedDefer = $q.defer();

    $rootScope.gassman = {
        loggedUser: null,
        selectedCsa: null,
        csa:null,
        selectedAccount: null,
        appStarted: appStartedDefer.promise,
        userLoading: false,
        csaLoading: false
    };

    var userLoading = null;
    var csaLoading = null;

    $rootScope.$watch('gassman.selectedCsa', function (v) {

        if (userLoading == null) {
            userLoading = $q.defer();

            $rootScope.gassman.userLoading = userLoading.promise;
        }

        // quando cambia csa devo ricaricare il profilo perché
        // cambiano conti e permessi

        $rootScope.gassman.csa = $rootScope.gassman.csaError = null;

        if (v != null) {
            if (csaLoading == null) {
                csaLoading = $q.defer();

                $rootScope.gassman.csaLoading = csaLoading.promise;
            }

            gdata.csaInfo(v)
            .then(function (r) {
                $rootScope.gassman.csa = r.data;
                $rootScope.gassman.csa.kitty.membership_fee = parseFloat($rootScope.gassman.csa.kitty.membership_fee);
                $rootScope.gassman.csa.default_account_threshold = parseFloat($rootScope.gassman.csa.default_account_threshold);
            }).then(undefined, function (error) {
                if (error[0] != gdata.error_codes.E_no_csa_found)
                    $rootScope.gassman.csaError = error;
            }).finally(function () {
                csaLoading.resolve(false);
                csaLoading = null;
            });
        } else {
            $rootScope.gassman.csa = null;
            $rootScope.gassman.csaLoading = false;
            csaLoading = null;
        }

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
            console.log('azz, ma gestito altrove', error);
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
