/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaAdmin', [
	'GassmanApp.services.Gdata'
])

.controller('CsaAdmin', [
         '$scope', '$filter', '$location', '$routeParams', 'gdata', '$q',
function ($scope,   $filter,   $location,   $routeParams,   gdata,   $q) {
	var csaId = $routeParams['csaId'];

	$scope.profile = null;
	$scope.csa = null;
	$scope.loadError = null;
	$scope.draftOrders = null;

	$scope.saveCsa = function () {
		$scope.saveError = null;

		gdata.csaUpdate($scope.csa).then (function (r) {
			$location.path('/csa/' + csaId + '/detail');
		}).then (undefined, function (error) {
			$scope.saveError = error;
		});
	};

	$scope.cancel = function () {
		$location.path('/csa/' + csaId + '/detail');
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

		return gdata.csaInfo(csaId);
	}).
	then (function (r) {
		$scope.csa = r.data;
		$scope.csa.kitty.membership_fee = parseFloat($scope.csa.kitty.membership_fee);

		$scope.csa.default_account_threshold = parseFloat($scope.csa.default_account_threshold);

		// TODO: in realtà degli ordini CPY mi interessano solo le mie ordinazioni!!
		return gdata.accountAmount($scope.csa.kitty.id);
	}).
	then (function (r) {
		$scope.csa.kitty.amount = r.data;
	}).
	then (undefined, function (error) {
		$scope.loadError = error.data;
	});
}])
;