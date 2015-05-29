/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaDetail', [
	'GassmanApp.services.Gdata'
])

.controller('CsaDetail', [
         '$scope', '$filter', '$location', '$routeParams', 'gdata', '$q',
function ($scope,   $filter,   $location,   $routeParams,   gdata,   $q) {
	var csaId = $routeParams['csaId'];

	$scope.profile = null;
	$scope.csa = null;
	$scope.loadError = null;
	$scope.openOrders = null;
	//$scope.openOrdersError = null;
	$scope.deliveringOrders = null;
	//$scope.deliveringOrdersError = null;
	$scope.draftOrders = null;
	$scope.movements = null;

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/detail');
	};

	$scope.showTransaction = function (mov) {
		$location.path('/transaction/' + mov[4]);
	};

	$scope.showChargeMembershipFeeForm = function (v) {
		$scope.viewChargeMembershipForm = v;
	};

	$scope.chargeMembershipFee = function () {
		$scope.membershipFeeError = null;

		var v = $scope.csa.kitty.membership_fee;

		if (v > 0) {
			gdata.chargeMembershipFee(csaId, {
				amount: v,
				kitty: $scope.csa.kitty.id,
				description: $scope.csa.kitty.charge_description
			}).
			then (function (r) {
				$location.path('/transaction/' + r.data.tid);
			}).
			then (undefined, function (error) {
				$scope.membershipFeeError = error.data;
			});
		} else {
			$scope.membershipFeeError = 'negative';
		}
	};

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;

		$scope.editableMembershipFee = $scope.profile.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;

		return $q.all([ gdata.csaInfo(csaId),
		                gdata.accountByCsa(csaId)
		                ]);
	}).
	then (function (r) {
		$scope.csa = r[0].data;
		$scope.csa.kitty.membership_fee = parseFloat($scope.csa.kitty.membership_fee);
		$scope.accId = r[1];

		// TODO: in realtà degli ordini CPY mi interessano solo le mie ordinazioni!!
		return $q.all([
				gdata.accountMovements($scope.accId, 0, 5),
				gdata.accountAmount($scope.csa.kitty.id),
				gdata.accountAmount($scope.accId),
				//gdata.accountMovements($scope.csa.kitty.id, 0, 5),
				]);
	}).
	then (function (rr) {
		$scope.movements = rr[0].data;
		$scope.csa.kitty.amount = rr[1].data;
		$scope.personalAmount = rr[2].data;
		//$scope.csa.kitty.movements = rr[2].data;
	}).
	then (undefined, function (error) {
		$scope.loadError = error.data;
	});
}])
;
