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
         '$scope', '$filter', '$location', '$localStorage', 'gdata',
function ($scope,   $filter,   $location,   $localStorage,   gdata) {
	$scope.accounts = [];
	$scope.accountsError = null;
	$scope.queryFilter = $localStorage.accountIndex_queryFilter || '';
	$scope.queryOrder = 0;
	$scope.profile = null;
	$scope.profileError = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = $scope.queryFilter;
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;
		$localStorage.accountIndex_queryFilter = $scope.queryFilter;

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

	$scope.loadMore = function () {
		if ($scope.concluded || loading) return;

        loading = true;

		gdata.accountsIndex(currCsa, lastQuery, lastQueryOrder, start, blockSize).
		then(function (r) {
            loading = false;
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.accounts = $scope.accounts.concat(r.data);

			angular.forEach(r.data, function (e) {
				e.accountData = !!e[4];
			});

			if ($scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) == -1)
				return;

			angular.forEach(r.data, function (e) {
				if (e.profile)
					return;
				var pid = e[0];
				gdata.profile(currCsa, pid).
				then(function (p) {
					e.profile = p;
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
		if ($scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) == -1) {
			$location.path('/account/' + accountId + '/detail');
		} else {
			$location.path('/person/' + personId + '/detail');
		}
	};

	gdata.selectedCsa().
	then (function (csaId) {
		currCsa = csaId;
		return gdata.profileInfo();
	}).
	then (function (pData) {
		$scope.profile = pData;
		$scope.loadMore();
	}).
	then (undefined, function (error) {
		$scope.profileError = error.data;
	});
}])
;
