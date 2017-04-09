/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AccountsIndex', [
    'GassmanApp.services.Gdata',
    'GassmanApp.services.listController',
    'ngStorage',
    'GassmanApp.filters.HumanTimeDiff',
    'GassmanApp.filters.AlphaTimeDiff'
])


.controller('AccountsIndex', [
         '$scope', '$state', '$location', 'gdata', '$localStorage', 'listController',
function ($scope,   $state,   $location,   gdata,   $localStorage,   listController) {
    var showContacts = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) != -1;

    $scope.editableMembershipFee = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;

	listController.setupScope(
		$scope,
		// data service
		function (from, pageSize, filterBy) {
			return gdata.accountsIndex(
                $scope.gassman.selectedCsa,
                filterBy,
                from, pageSize);
		},
        // options
        {
            pageLoadedHook: function () {
                angular.forEach($scope.items, function (e) {
                    e.accountData = !!e[4];

                    if (!showContacts) {
                        e.profile = {};
                        e.profile.gadgets = [];

                        if (e[5] < 0 &&
                            e.profile.gadgets.indexOf(gdata.gadgets.debt) == -1
                        ) { // FIXME: la threshold dovrebbe essere un parametro del csa
                            e.profile.gadgets.push(gdata.gadgets.debt)
                        }
                    }
                });

                if (!showContacts)
                    return;

                angular.forEach($scope.items, function (e) {
                    if (e.profile)
                        return;
                    var pid = e[0];
                    gdata.profile($scope.gassman.selectedCsa, pid).
                    then(function (p) {
                        e.profile = p;

                        if (e[5] < 0 && // FIXME: la threshold dovrebbe essere un parametro del csa
                            e.profile.gadgets.indexOf(gdata.gadgets.piggyBank) == -1 &&
                            e.profile.gadgets.indexOf(gdata.gadgets.debt) == -1
                        ) {
                            e.profile.gadgets.push(gdata.gadgets.debt)
                        }
                    });
                });
            },
            filterBy: {
                q: /*FIXME: ripristinare $localStorage.accountIndex_queryFilter ||*/ '',
                o: '0',
                dp: '-1',
                ex: false
            },
            storage: $localStorage,
            storageKey: 'accounts_index'
        }
    );

    if ($scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canCheckAccounts) != -1) {
        $scope.orderBy = [
            { value: '0', label: 'nome' },
            { value: '1', label: 'saldo' },
            { value: '2', label: 'attività' }
        ];
    }

    $scope.showAccount = function (accountId, personId) {
        if ($scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) == -1) {
            $location.path('/account/' + accountId + '/detail');
        } else {
            $location.path('/person/' + personId + '/detail');
        }
    };

    $scope.toggleMembership = function (evt, item) {
        evt.stopPropagation();

        var origFee = item[8];
        var newFee = origFee > 0.0 ? 0.0 : 1.0;

        item[8] = newFee;
        item.updatingFee = true;

        gdata.setMembershipFee($scope.gassman.selectedCsa, item[0], newFee).then(function (r) {
            item.updatingFee = false;
        }).then(undefined, function (error) {
            item[8] = origFee;
            item.updatingFee = false;
        });
    };

    gdata.deliveryPlaces($scope.gassman.selectedCsa).
    then (function (resp) {
        $scope.deliveryPlaces = resp.data;
        if ($scope.deliveryPlaces.length > 1) {
            $scope.deliveryPlaces.unshift({ id: -1, description: 'Tutti' });
            $scope.deliveryPlaces.push({ id: -2, description: 'Non noto' });
        }
    }).
    then (undefined, function (error) {
        //$scope.initError = error.data;
        console.log('delivery places not available', error);
        $scope.deliveryPlaces = null;
    });
}])
;
