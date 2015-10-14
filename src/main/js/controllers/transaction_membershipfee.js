/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionMembershipFee', [
	'GassmanApp.services.Gdata'
])

.controller('TransactionMembershipFee', [
         '$scope', '$routeParams', '$location', '$timeout', 'gdata',
function ($scope,   $routeParams,   $location,   $timeout,   gdata) {

	$scope.savePayment = function () {
		if ($scope.$invalid ||
			$scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'f',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		angular.forEach($scope.trans.clients, function (l) {
			if (l.amount > 0.0) {
				if (l.account) {
					data.lines.push({
						amount: - l.amount,
						account: l.account,
						notes: l.notes
					});
				}
			}
		});
/*
		f = +1;
		angular.forEach($scope.trans.producers, cc);
		angular.forEach($scope.trans.expenses, function (l) {
			// a differenza di clienti e produttori, qui non ho il conto:
			// lo inserisce il server in base a csa e currency
			if (l.amount > 0.0) {
				data.lines.push({
					amount: l.amount,
					notes: l.notes,
					account: null
				});
			}
		});
*/
		if (data.lines.length == 0) {
			return;
		}

		data.lines.push({
			amount: +1, // TANTO VIENE CALCOLATO
			account: 'KITTY',
			notes: ''
		});

		//data = angular.toJson(data) // lo fa già in automatico
		gdata.transactionSave($scope.csaId, data).
		then (function (r) {
			//console.log('TransactionPayment: save result:', r);
			//$scope.savedTransId = r.data;
			//$scope.transId = 'new';
			//$scope.lines = [];
			//$scope.producers = [];
			//$scope.expenses = [];
			//$scope.accounts = {};
			//$scope.tsaveOk = true;

			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
}])
;