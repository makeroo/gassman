/**
 * Created by makeroo on 05/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionPayment', [
	'GassmanApp.services.Gdata'
])

.controller('TransactionPayment', [
         '$scope', '$routeParams', '$location', '$timeout', 'gdata',
function ($scope,   $routeParams,   $location,   $timeout,   gdata) {

	$scope.savePayment = function () {
		if ($scope.$invalid || $scope.currencyError)
			return;

		var data = {
			transId: $scope.trans.transId == 'new' ? null : $scope.trans.transId,
			cc_type: 'p',
			currency: $scope.currency[0],
			lines: [],
			date: $scope.trans.tdate,
			description: $scope.trans.tdesc
		};

		var f = -1;
		var cc = function (l) {
			if (l.amount > 0.0 && l.account) {
                data.lines.push({
                    amount: l.amount * f,
                    account: l.account,
                    notes: l.notes
                });
			}
		};

        var kittyId = $scope.kittyId();

		angular.forEach($scope.trans.clients, cc);

		f = +1;
		angular.forEach($scope.trans.producers, cc);

        data.lines = data.lines.concat($scope.trans.expenses);

		angular.forEach($scope.trans.kittyLines, function (l) {
            if (l.amount > 0.0 || l.amount < 0.0) { // nb: può essere null
                if (!l.account || l.account == 'KITTY') {
                    l.account = kittyId;
                }

                data.lines.push(l);
            }
        });

		if (data.lines.length == 0) {
			return;
		}

        if (! $scope.amountEquals($scope.difference, 0.0)) {
            data.lines.push({
                amount: - $scope.difference,
                account: kittyId,
                notes: ''
            });
        }

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
