/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.PersonDetail', [
    'GassmanApp.services.Gdata'
])

.controller('PersonDetail', [
         '$scope', '$filter', '$stateParams', '$location', 'gdata', '$q',
function ($scope,   $filter,   $stateParams,   $location,   gdata,   $q) {
    $scope.personProfile = null;
    $scope.personProfileError = null;
    $scope.editable = false;
    $scope.saveError = null;
    //$scope.membership_fee = null;

    var master = null;
    var personId = $stateParams.personId;
    var self = $scope.gassman.loggedUser.profile.id == personId;

    $scope.readOnly = personId != $scope.gassman.loggedUser.profile.id;

    $scope.accountClose = true;
    angular.forEach($scope.gassman.loggedUser.accounts, function (a) {
        if (a.to_date == null)
            $scope.accountClose = false;
    });

/*
    $scope.visibleAddress = function (c) {
        return c.kind !== 'I';
    };
*/
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
        return a.csa_id == $scope.gassman.selectedCsa;
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

        var savedContacts = {}
        $scope.personProfile.contacts = f($scope.personProfile.contacts, function (c) {
            if (!c.address)
                return false;
            var savedContact = [c.address, c.kind, c.contact_type];
            if (savedContact in savedContacts)
                return false;
            savedContacts[savedContact] = true;
            return true;
        });

        gdata.saveProfile($scope.gassman.selectedCsa, $scope.personProfile).
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

    $scope.closeAccount = function (accountId) {
        if (!confirm('Confermi?')) // FIXME: rifare i popup in html
            return;

        gdata.closeAccount(accountId, personId, 'Chiusura conto' /*FIXME: localizzare*/).then (
            loadPersonProfileAndAccounts
        ).then (undefined, function (error) {
            // TODO: show error
        });
    };

    $scope.requestMembership = function (csa) {
        gdata.requestMembership(csa).
        then (function (r) {
            $scope.membershipRequested = true;
        }).
        then (undefined, function (error) {
            $scope.membershipRequestedError = error.data;
        });
    };

    function loadPersonProfileAndAccounts () {
        return gdata.profile($scope.gassman.selectedCsa, personId).then (function (p) {
            $scope.personProfile = p;
            if ($scope.personProfile.profile.default_delivery_place_id != null) {
                $scope.personProfile.profile.default_delivery_place_id = '' + $scope.personProfile.profile.default_delivery_place_id;
            }
            $scope.editable = (
                $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditContacts) != -1 ||
                self
            );

            var amounts = [];
            angular.forEach($scope.personProfile.accounts, function (a) {
                amounts.push(gdata.accountAmount(a.id));
            });

            return $q.all(amounts);
        }).then (function (amounts) {
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

                    $scope.canEditMembershipFee = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;
                    $scope.canCloseAccounts = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canCloseAccounts) != -1;

                    $scope.personProfile.membership_fee = {
                        //account: acc.id,
                        amount: parseFloat(acc.membership_fee)
                    };
                }
            }
        });
    }

    if ($scope.gassman.selectedCsa) {
        gdata.deliveryPlaces($scope.gassman.selectedCsa)
        .then(function (r) {
            $scope.deliveryPlaces = r ? r.data : [];

            return loadPersonProfileAndAccounts();
        }).then(undefined, function (error) {
            if (error.data[0] != gdata.error_codes.E_permission_denied)
                $scope.personProfileError = error.data || error;
            else
                return loadPersonProfileAndAccounts();
        }).then(function () {
            if ($scope.accountClose)
                return loadCsaList();
        }).then(undefined, function (error) {
            $scope.personProfileError = error.data || error;
        });
    } else {
        loadCsaList();
    }

    function loadCsaList () {
        $scope.personProfile = angular.copy($scope.gassman.loggedUser);

        gdata.csaList()
        .then(function (csaList) {
            $scope.editable = true;

            $scope.csaList = csaList.data;
        }).then(undefined, function (error) {
            $scope.personProfileError = error.data || error;
        });
    }
}])
;
