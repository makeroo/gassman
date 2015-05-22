/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionWithdrawal', [
    'gassmanServices'
])

.controller('TransactionWithdrawal', [
         '$scope', '$routeParams', '$location', '$timeout', 'gdata', 'accountAutocompletion',
function ($scope,   $routeParams,   $location,   $timeout,   gdata,   accountAutocompletion) {

	$scope.saveWithdrawal = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'w',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.clients, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionWithdrawal: save result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
}])
;
