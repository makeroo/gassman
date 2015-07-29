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

.controller('AccountsIndex', [
         '$scope', '$filter', '$location', '$localStorage', '$q', 'gdata',
function ($scope,   $filter,   $location,   $localStorage,   $q,   gdata) {
	$scope.accounts = [];
	$scope.accountsError = null;
//	$scope.queryFilter = $localStorage.accountIndex_queryFilter || '';
//	$scope.queryOrder = 0;
	$scope.profile = null;
	$scope.profileError = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = {
		q: $localStorage.accountIndex_queryFilter || '',
		o: 0,
		dp: -1
	};
//	var lastQuery = ;
//	var lastQueryOrder = 0;
//	var lastDeliveryPlace = -1;

	$scope.query = angular.copy(lastQuery);

	$scope.search = function () {
		if (currCsa == null || angular.equals($scope.query, lastQuery))
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

	var currCsa = null;
    var loading = false;

	$scope.$watch('query.dp', $scope.search);

	$scope.loadMore = function () {
		if ($scope.concluded || loading) return;

        loading = true;

		gdata.accountsIndex(
			currCsa,
			lastQuery,
			start, blockSize).
		then(function (r) {
            loading = false;
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.accounts = $scope.accounts.concat(r.data);

			var showContacts = $scope.profile.permissions.indexOf(gdata.permissions.P_canViewContacts) != -1;

			angular.forEach(r.data, function (e) {
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

			angular.forEach(r.data, function (e) {
				if (e.profile)
					return;
				var pid = e[0];
				gdata.profile(currCsa, pid).
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
		}).
		then (undefined, function (error) {
            loading = false;
			$scope.concluded = true;
			$scope.accountsError = error.data;
		});
	};

	$scope.showAccount = function (accountId, personId) {
		if ($scope.profile.permissions.indexOf(gdata.permissions.P_canViewContacts) == -1) {
			$location.path('/account/' + accountId + '/detail');
		} else {
			$location.path('/person/' + personId + '/detail');
		}
	};

	gdata.selectedCsa().
	then (function (csaId) {
		currCsa = csaId;
		return $q.all([ gdata.profileInfo(), gdata.deliveryPlaces(csaId) ]);
	}).
	then (function (resp) {
		$scope.profile = resp[0];
		$scope.deliveryPlaces = resp[1].data;
		if ($scope.deliveryPlaces.length > 1) {
			$scope.deliveryPlaces.unshift({ id: -1, description: 'Tutti' });
		}
		$scope.loadMore();
	}).
	then (undefined, function (error) {
		$scope.profileError = error.data;
	});
}])
;
