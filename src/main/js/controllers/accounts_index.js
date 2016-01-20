/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AccountsIndex', [
    'GassmanApp.services.Gdata',
    'ngStorage',
    'GassmanApp.filters.HumanTimeDiff',
    'GassmanApp.filters.AlphaTimeDiff'
])

.service('listController',
[
function () {
	this.setupScope = function ($scope, dataService, options) {
        options = options || {};

        if (options.storage)
            $scope.pagination = options.storage[options.storageKey];

        if (!$scope.pagination)
            $scope.pagination = {
                totalItems: 0,
                page: options.firstPage || 1,
                pageSize: (+options.pageSize || 15).toString(),
                filterBy: options.filterBy,
                pageSizes: options.pageSizes || [ 15, 30, 60, 100 ]
            };

		$scope.items = null;
		$scope.initError = null;
		$scope.pageError = null;

		$scope.$watch('pagination.page', function (n, o) {
			if ($scope.pagination.page > 0 && o != n) {
				$scope.loadPage($scope.pagination.page);
			}
		});

		$scope.$watch('pagination.pageSize', function (n, o) {
			if (n > 0 && n != o) {
				$scope.pageCount = null;
				$scope.loadPage(1);
			}
		});

		$scope.$watch('pagination.filterBy', function (n, o) {
            //questo serve a evitare il doppio ricaricamento della pagina in caso di filtro e pagina corrente != dalla prima
            if (n == o) {
                return;
            } else if ($scope.pagination.page != 1) {
                $scope.pagination.page = 1;
            } else {
                $scope.loadPage(1);
            }
		}, true);

		$scope.loadPage = function (p) {
            if (options.storage) {
                options.storage[options.storageKey] = angular.copy($scope.pagination);
            }

			$scope.pagination.page = p;

            var sz = +$scope.pagination.pageSize;
			var from = (p - 1) * sz;

			dataService(from, sz, $scope.pagination.filterBy).
			then (function (r) {
                $scope.pagination.totalItems = r.data.count;
				$scope.items = r.data.items;

				if (options) {
                    try {
                        options.pageLoadedHook();
                    } catch (e) {
                        console.log('pageLoadedHook failed', e);
                    }
				}
			}).
			then (undefined, function (error) {
				$scope.pageError = error.data;
			});
		};

        if (options.loadFirstPage !== false) {
            $scope.loadPage($scope.pagination.page);
        }
	};
}])

.controller('AccountsIndex', [
         '$scope', '$state', '$location', 'gdata', '$localStorage', 'listController',
function ($scope,   $state,   $location,   gdata,   $localStorage,   listController) {
    var showContacts = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) != -1;

	listController.setupScope(
		$scope,
		// data service
		function (from, pageSize, filterBy) {
			return gdata.accountsIndex(
                $scope.gassman.selectedCsa,
                filterBy,
                from, pageSize);
		},
        // options
        {
            pageLoadedHook: function () {
                angular.forEach($scope.items, function (e) {
                    e.accountData = !!e[4];

                    if (!showContacts) {
                        e.profile = {};
                        e.profile.gadgets = [];

                        if (e[5] < 0 &&
                            e.profile.gadgets.indexOf(gdata.gadgets.debt) == -1
                        ) { // FIXME: la threshold dovrebbe essere un parametro del csa
                            e.profile.gadgets.push(gdata.gadgets.debt)
                        }
                    }
                });

                if (!showContacts)
                    return;

                angular.forEach($scope.items, function (e) {
                    if (e.profile)
                        return;
                    var pid = e[0];
                    gdata.profile($scope.gassman.selectedCsa, pid).
                    then(function (p) {
                        e.profile = p;

                        if (e[5] < 0 && // FIXME: la threshold dovrebbe essere un parametro del csa
                            e.profile.gadgets.indexOf(gdata.gadgets.piggyBank) == -1 &&
                            e.profile.gadgets.indexOf(gdata.gadgets.debt) == -1
                        ) {
                            e.profile.gadgets.push(gdata.gadgets.debt)
                        }
                    });
                });
            },
            filterBy: {
                q: /*FIXME: ripristinare $localStorage.accountIndex_queryFilter ||*/ '',
                o: '0',
                dp: '-1',
                ex: false
            },
            storage: $localStorage,
            storageKey: 'accounts_index'
        }
    );

    if ($scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canCheckAccounts) != -1) {
        $scope.orderBy = [
            { value: '0', label: 'nome' },
            { value: '1', label: 'saldo' },
            { value: '2', label: 'attività' }
        ];
    }

    $scope.showAccount = function (accountId, personId) {
        if ($scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) == -1) {
            $location.path('/account/' + accountId + '/detail');
        } else {
            $location.path('/person/' + personId + '/detail');
        }
    };

    gdata.deliveryPlaces($scope.gassman.selectedCsa).
    then (function (resp) {
        $scope.deliveryPlaces = resp.data;
        if ($scope.deliveryPlaces.length > 1) {
            $scope.deliveryPlaces.unshift({ id: -1, description: 'Tutti' });
            $scope.deliveryPlaces.push({ id: -2, description: 'Non noto' });
        }
    }).
    then (undefined, function (error) {
        //$scope.initError = error.data;
        console.log('delivery places not available', error);
        $scope.deliveryPlaces = null;
    });
}])
/*
.controller('AccountsIndex', [
         '$scope', '$filter', '$localStorage', '$q', 'gdata',
function ($scope,   $filter,   $location,   ,   $q,   gdata) {
    $scope.accounts = [];
    $scope.accountsError = null;
//	$scope.queryFilter = $localStorage.accountIndex_queryFilter || '';
//	$scope.queryOrder = 0;

    var start = 0;
    var blockSize = 25;
    $scope.concluded = false;

//	var lastQuery = ;
//	var lastQueryOrder = 0;
//	var lastDeliveryPlace = -1;

    $scope.query = angular.copy(lastQuery);

    $scope.search = function () {
        if (angular.equals($scope.query, lastQuery))
            return;

        lastQuery = angular.copy($scope.query);

        $localStorage.accountIndex_queryFilter = $scope.query.q;

        reset();
        $scope.loadMore();
    };

    var reset = function () {
        $scope.accounts = [];
        $scope.accountsError = null;
        start = 0;
        $scope.concluded = false;
    };

    var loading = false;

    $scope.$watch('query.dp', $scope.search);

    $scope.loadMore = function () {
        if ($scope.concluded || loading) return;

        loading = true;

        gdata.accountsIndex(
            $scope.gassman.selectedCsa,
            lastQuery,
            start, blockSize).
        then(function (r) {
            loading = false;
            $scope.concluded = r.data.length < blockSize;
            start += r.data.length;
            $scope.accounts = $scope.accounts.concat(r.data);

        }).
        then (undefined, function (error) {
            loading = false;
            $scope.concluded = true;
            $scope.accountsError = error.data;
        });
    };
}])
*/
;
