/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionMembershipFee', [
	'GassmanApp.services.Gdata'
])

.controller('TransactionMembershipFee', [
         '$scope', 'gdata',
function ($scope,   gdata) {

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
			$scope.showTransaction(r.data);
		}).
		then (undefined, function (error) {
			$scope.tsaveError = error.data;
		});
	};
}])
;
