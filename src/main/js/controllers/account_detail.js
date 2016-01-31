/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AccountDetail', [
    'GassmanApp.services.Gdata',
    'GassmanApp.services.listController',
    'ngStorage'
])

.controller('AccountDetail', [
        '$scope', '$filter', '$stateParams', '$location', 'gdata', '$localStorage', 'listController',
function($scope,   $filter,   $stateParams,   $location,   gdata,   $localStorage,   listController) {

    var accId = $stateParams.accountId;

    $scope.viewableContacts = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) != -1;
    $scope.accountOwnerError = null;
    $scope.accountOwner = null;
    $scope.accountDesc = null;
    $scope.amount = null;

    $scope.showTransaction = function (mov) {
        $location.path('/transaction/' + mov[4]);
    };

    $scope.accId = accId;

    gdata.accountOwner(accId).
    then (function (r) {
        if (r.data.people)
            $scope.accountOwner = r.data.people;
        else
            $scope.accountDesc = r.data.desc;
    }).
    then (undefined, function (error) {
        $scope.accountOwnerError = error.data;
    });

    gdata.accountAmount(accId)
    .then(function (r) {
        $scope.amount = r.data;
    })
    .then(undefined, function (error) {
        $scope.accountOwnerError = error.data;
    });

    listController.setupScope(
        $scope,
        // data service
        function (from, pageSize, filterBy) {
            return gdata.accountMovements($scope.accId, filterBy, from, pageSize);
        },
        // options
        {
            filterBy: '',
            storage: $localStorage,
            storageKey: 'account_detail_' + $scope.accId
        }
    );
}])
;
