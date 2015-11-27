/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionCashExchange', [
	'GassmanApp.services.Gdata'
])

.controller('TransactionCashExchange', [
         '$scope', '$location', '$timeout', 'gdata',
function ($scope,   $location,   $timeout,   gdata) {
	$scope.saveCashExchange = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'x',
			currency: $scope.currency[0],
			lines: [],
			//receiver: $scope.trans.clients[0].account,
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.producers, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push(l);
				}
			}
		});

		if (data.lines.length == 0) {
			return;
		}

		data.lines.push({
			account: $scope.trans.clients[0].account,
			amount: -1, // tanto poi viene corretto da backend
			notes: ''
		});

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionCashExchange: save result:', r);

			$scope.showTransaction(r.data);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.tsaveOk = true;
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
}])
;
