/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaAdmin', [
    'GassmanApp.services.Gdata'
])

.controller('CsaAdmin', [
         '$scope', '$filter', '$location', '$transition$', 'gdata', '$q',
function ($scope,   $filter,   $location,   $transition$,   gdata,   $q) {
    var csaId = $transition$.params().csaId;

    $scope.draftOrders = null;

    $scope.saveCsa = function () {
        $scope.saveError = null;

        gdata.csaUpdate($scope.gassman.csa).then (function (r) {
            $location.path('/csa/' + csaId + '/detail');
        }).then (undefined, function (error) {
            $scope.saveError = error;
        });
    };

    $scope.showAccount = function (accountId) {
        $location.path('/account/' + accountId + '/detail');
    };

    $scope.cancel = function () {
        $location.path('/csa/' + csaId + '/detail');
    };

    $scope.showChargeMembershipFeeForm = function (v) {
        $scope.viewChargeMembershipForm = v;
    };

    $scope.chargeMembershipFee = function () {
        $scope.membershipFeeError = null;

        var v = $scope.gassman.csa.kitty.membership_fee;

        if (v > 0) {
            gdata.chargeMembershipFee(csaId, {
                amount: v,
                kitty: $scope.gassman.csa.kitty.id,
                description: $scope.gassman.csa.kitty.charge_description
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

    $scope.editableMembershipFee = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;

    $q.when($scope.csaInfo).then(function () {
        // TODO: in realtà degli ordini CPY mi interessano solo le mie ordinazioni!!
        return gdata.accountAmount($scope.gassman.csa.kitty.id);
    }).
    then (function (r) {
        $scope.gassman.csa.kitty.amount = r.data;
    }).
    then (undefined, function (error) {
        $scope.loadError = error.data;
    });
}])
;
