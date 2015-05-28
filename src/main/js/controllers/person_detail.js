/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.PersonDetail', [
	'GassmanApp.services.Gdata'
])

.controller('PersonDetail', [
         '$scope', '$filter', '$routeParams', '$location', 'gdata', '$q',
function ($scope,   $filter,   $routeParams,   $location,   gdata,   $q) {
	$scope.csaId = null;
	$scope.personProfile = null;
	$scope.personProfileError = null;
	$scope.readOnly = true;
	$scope.editable = false;
	$scope.saveError = null;
	//$scope.membership_fee = null;

	var master = null;
	var personId = $routeParams['personId'];
/*
	$scope.visibleAddress = function (c) {
		return c.kind !== 'I';
	};
*/
	$scope.addressKind = function (k) {
		return function (c) {
			return c.kind == k;
		}
	};
	$scope.hasAddressOfKind = function (k) {
		if (!$scope.personProfile)
			return false;
		for (var i in $scope.personProfile.contacts) {
			if ($scope.personProfile.contacts[i].kind == k)
				return true;
		}
		return false;
	};

	$scope.visibleAccount = function (a) {
		return a.csa_id == $scope.csaId;
	};

	$scope.modify = function () {
		if ($scope.readOnly) {
			master = angular.copy($scope.personProfile);
			$scope.readOnly = false;
			$scope.saveError = null;
		}
	};

	$scope.isUnchanged = function () {
		return angular.equals($scope.personProfile, master);
	};

	$scope.save = function () {
		var f = $filter('filter');
		var cc = f($scope.personProfile.contacts, function (c) {
			return !!c.address;
		})

		$scope.personProfile.contacts = cc;

		gdata.saveProfile($scope.csaId, $scope.personProfile).
		then (function (r) {
			$scope.readOnly = true;
			//if ($scope.personProfile.membership_fee)
			//	$scope.membership_fee = $scope.personProfile.membership_fee.amount;
		}).
		then (undefined, function (error) {
			console.log('PersonDetail: saveProfile error:', error);
			$scope.saveError = error.data;
		});
	};

	$scope.cancel = function () {
		if (!$scope.readOnly) {
			$scope.readOnly = true;
			$scope.personProfile = master;
		}
	};

	$scope.addContact = function (k) {
		$scope.personProfile.contacts.push({
			address: '',
			kind: k,
			contact_type: '',
			id: -1,
			priority: 0,
			person_id: $scope.personProfile.profile.id
		});
	};

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/detail');
	};

	gdata.profileInfo().
	then (function (p) {
		$scope.profile = p;

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;

		return gdata.profile(csaId, personId);
	}).
	then (function (prof) {
		$scope.personProfile = prof;
		$scope.editable = $scope.profile.permissions.indexOf(gdata.permissions.P_canEditContacts) != -1 ||
			personId == $scope.profile.logged_user.id;

		var amounts = [];
		angular.forEach($scope.personProfile.accounts, function (a) {
			amounts.push(gdata.accountAmount(a.id));
		});

		return $q.all(amounts);
	}).
	then (function (amounts) {
		var l = amounts.length;

		for (var c = 0; c < l; ++c) {
			var acc = $scope.personProfile.accounts[c];
			var am = amounts[c];
			acc.amount = am.data[0];
			acc.csym = am.data[1];

			if (acc.to_date == null) {
				// nb: qui assumo una sola moneta per gas... FIXME
				//$scope.membership_fee = acc.membership_fee;
				//$scope.aka_csym = acc.csym;

				$scope.canEditMembershipFee = $scope.profile.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;

					$scope.personProfile.membership_fee = {
						//account: acc.id,
						amount: parseFloat(acc.membership_fee),
					};
			}
		}
	}).
	then (undefined, function (error) {
		$scope.personProfileError = error.data;
	});
}])
;
