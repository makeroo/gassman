/**
 * Created by makeroo on 04/05/15.
 */

'use strict';

angular.module('GassmanApp.controllers.TransactionsIndex', [
    'GassmanApp.services.Gdata',
    'GassmanApp.services.listController',
    'ngStorage'
])

.controller('TransactionsIndex', [
         '$scope', '$location', 'gdata', '$localStorage', 'listController',
function ($scope,   $location,   gdata,   $localStorage,   listController) {
    listController.setupScope(
        $scope,
        // data service
        function (from, pageSize, filterBy) {
            return gdata.transactionsLog($scope.gassman.selectedCsa, filterBy.queryFilter, filterBy.queryOrder, from, pageSize);
        },
        // options
        {
            filterBy: {
                queryFilter: '',
                queryOrder: '0'
            },
            storage: $localStorage,
            storageKey: 'transactions_index'
        }
    );

    $scope.showTransaction = function (tl) {
        $location.path('/transaction/' + tl[3]);
    };
}])
;
