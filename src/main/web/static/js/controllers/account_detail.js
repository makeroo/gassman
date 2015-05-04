/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AccountDetail', [
    'gassmanServices'
])

.controller('AccountDetail', [
        '$scope', '$filter', '$routeParams', '$location', 'gdata',
function($scope,   $filter,   $routeParams,   $location,   gdata) {
	$scope.movements = [];
	$scope.movementsError = null;
	$scope.accountOwner = null;
	$scope.accountDesc = null;
	$scope.accountOwnerError = null;
	$scope.amount = null;
	$scope.viewableContacts = false;
//	$scope.selectedMovement = null;

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var accId = $routeParams['accountId'];
	var start = 0;
	var blockSize = 25;
	var concluded = false;

	var showOwner = function (accId) {
		$scope.accId = accId;
		gdata.accountOwner(accId).
		then (function (r) {
			if (r.data.people)
				$scope.accountOwner = r.data.people;
			else
				$scope.accountDesc = r.data.desc;
		}).
		then (undefined, function (error) {
			$scope.accountOwnerError = error.data;
		});
	};

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;
		$scope.viewableContacts = $scope.profile.permissions.indexOf(gassmanApp.P_canViewContacts) != -1;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;

		return accId || gdata.accountByCsa(csaId);
	}).
	then (function (accId) {
		showOwner(accId);
		$scope.loadMore();

		return gdata.accountAmount(accId);
	}).
	then (function (r) {
		$scope.amount = r.data;
	}).
	then (undefined, function (error) {
		$scope.accountOwnerError = error.data;
	});

	$scope.showTransaction = function (mov) {
		$location.path('/transaction/' + mov[4]);
	};

	$scope.loadMore = function () {
		if (concluded) return;

		gdata.accountMovements($scope.accId, start, blockSize).
		then (function (r) {
			concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.movements = $scope.movements.concat(r.data);
		}).
		then (undefined, function (error) {
			concluded = true;
			// TODO: FIXME: qui ho 2 errori...
			$scope.serverError = error.data[1];
			console.log('AccountDetail: movements error:', error.data)
			$scope.showErrorMessage = false;
			$scope.movementsError = error.data;
			//console.log('error', data, status, headers, config);
		});
	};
}])
;
