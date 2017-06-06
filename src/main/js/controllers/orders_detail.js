'use strict';

angular.module('GassmanApp.controllers.OrdersDetail', [])

.controller('OrdersDetail', [
         '$scope', '$transition$', 'gdata', 'accountAutocompletion',
function ($scope,   $transition$,   gdata,   accountAutocompletion) {
    var orderId = $transition$.params().orderId;

    $scope.order = null; // innesco loading
    $scope.autocompletionData = null; // innesco loading

    $scope.addProduct = function () {
        $scope.order.products.push({
            id: null,
            description: '',
            quantities: [
            ]
        });
    };

    $scope.removeProduct = function (idx) {
        $scope.order.products.splice(idx, 1);
    };

    $scope.addQuantity = function (p) {
        p.quantities.push({
            id: null,
            description: '',
            amount: '0'
        });
    };

    $scope.removeQuantity = function (p, idx) {
        p.quantities.splice(idx, 1);
    };

    $scope.saveDraft = function () {
        $scope.saving = true;

        gdata.saveOrderDraft($scope.order).then(function (resp) {
            if ($scope.order.id == null) {
                $scope.order.id = resp.data[0];
                // TODO: si cambia url?
            }
        }).then(undefined, function (error) {
            $scope.saveError = error.data;
        }).finally(
            function () {
                $scope.saving = false;
            }
        );
    };

    gdata.accountsNames($scope.gassman.selectedCsa).then(function (r) {
        $scope.currencies = accountAutocompletion.parse(r.data);
        $scope.available_currencies = accountAutocompletion.available_currencies($scope.currencies);

        if ($scope.order.currency_id === null) {
            for (var i in $scope.available_currencies) {
                if ($scope.available_currencies.hasOwnProperty(i)) {
                    $scope.order.currency_id = i;
                    $scope.order.symbol = $scope.available_currencies[i];

                    break;
                }
            }
        }

        $scope.autocompletionData = accountAutocompletion.compose($scope.currencies);
    }).then(undefined, function (error) {
        $scope.orderLoadError = error.data;
    });

    if (gdata.isPk(orderId)) {
        gdata.order(orderId).then(function (r) {
            $scope.order = r.data;
        }).then(undefined, function (error) {
            $scope.orderLoadError = error.data;
        });
    } else if (orderId === 'new') {
        // TODO: recuperare currency

        $scope.order = {
            id: null,
            csa_id: $scope.gassman.selectedCsa,
            state: gdata.order_states.draft,
            description: '',
            notes: '',
            account_threshold: null,
            apply_account_threshold: false,
            profile_required: 'N',
            producer_id: null,
            currency_id: null,
            symbol: null,
            delivery: null,
            products: []
        };
    } else {
        // TODO: lanciare 404

        throw 'illegal url';
    }
}])
;
