/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.services.listController', [
])


.service('listController',
[
function () {
	this.setupScope = function ($scope, dataService, options) {
        options = options || {};

        if (options.storage)
            $scope.pagination = options.storage[options.storageKey];

        if (!$scope.pagination) {
            var sizes = options.pageSizes || [15, 30, 60, 100];
            $scope.pagination = {
                totalItems: 0,
                page: options.firstPage || 1,
                pageSize: (+options.pageSize || sizes[0]).toString(),
                filterBy: options.filterBy,
                pageSizes: sizes
            };
        }

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

				if (options && options.pageLoadedHook) {
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
;
