/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionsIndex', [
    'gassmanServices'
])

.controller('TransactionsIndex', [
         '$scope', '$location', 'gdata',
function ($scope,   $location,   gdata) {
	$scope.transactions = null;
	$scope.transactionsError = null;
	$scope.queryFilter = '';
	$scope.queryOrder = 0;
	$scope.loadError = null;
	$scope.lastTransId = null;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = '';
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;

		reset();
		$scope.loadMore();
	};

	var reset = function () {
		$scope.transactions = [];
		$scope.transactionsError = null;
		start = 0;
		$scope.concluded = false;
	};

	gdata.selectedCsa().
	then (function (csaId) { $scope.csaId = csaId; $scope.loadMore(); }).
	then (undefined, function (error) { $scope.loadError = error.data; });

	$scope.loadMore = function () {
		if ($scope.concluded) return;

		gdata.transactionsLog($scope.csaId, lastQuery, lastQueryOrder, start, blockSize).
		then (function (r) {
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.transactions = $scope.transactions == null ? r.data : $scope.transactions.concat(r.data);
		}).
		then (undefined, function (error) {
			$scope.concluded = true;
			$scope.loadError = error.data[1];
			console.log('TransactionIndex: transactionsLog error:', error.data);
		});
	};

	$scope.showTransaction = function (tl) {
		$location.path('/transaction/' + tl[3]);
	};
}])
;
