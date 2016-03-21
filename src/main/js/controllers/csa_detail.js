/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaDetail', [
    'ui.calendar',

    'GassmanApp.services.Gdata',
    'GassmanApp.controllers.CsaBase'
])

.controller('CsaDetail', [
         '$scope', '$filter', '$location', '$stateParams', 'gdata', '$q', '$uibModal', 'uiCalendarConfig',
function ($scope,   $filter,   $location,   $stateParams,   gdata,   $q,   $uibModal,   uiCalendarConfig) {
    var csaId = $stateParams.csaId;

    $scope.openOrders = null;
    //$scope.openOrdersError = null;
    $scope.deliveringOrders = null;
    //$scope.deliveringOrdersError = null;
    $scope.draftOrders = null;
    $scope.movements = null;

    $scope.calendar = {
        //height: 450,
        editable: false,
        header:{
            left: 'title', //month basicWeek basicDay agendaWeek agendaDay',
            //center: '',
            right: 'prev,next' // today
        },
        titleFormat: '[Turni] MMMM YYYY',
        eventClick: function (calEvent, jqueryEvent) {
            $scope.cal_info.selected_event = $scope.cal_info.prepare_event(calEvent.deliveryDate);
        }
        //dayClick: $scope.alertEventOnClick,
        //eventDrop: $scope.alertOnDrop,
        //eventResize: $scope.alertOnResize
    };

    $scope.addShift = function (shift) {
        var modalInstance = $uibModal.open({
            animation: true,
            templateUrl: 'template/new_shift.html',
            controller: 'AddShiftPopup',
            size: 'sm',
            resolve: {
                event: function () {
                    return $scope.cal_info.selected_event;
                },
                shift: function () {
                    return shift;
                }
            }
        });

        modalInstance.result.then(function (shiftAndRole) {
            console.log(shiftAndRole);

            var shift = shiftAndRole[0];
            var role = shiftAndRole[1];

            if (role === null) {
                if (shift !== undefined) {
                    gdata.removeShift($scope.gassman.selectedCsa, shift.id).then(function (r) {
                        uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
                    }).then(undefined, function (error) {
                        console.log(error); // TODO:
                    });
                }
            } else {
                if (shift === undefined || shift.role != role) {
                    gdata.addShift(
                        $scope.gassman.selectedCsa,
                        $scope.cal_info.selected_event.id,
                        shift ? shift.id : null,
                        role,
                        $scope.gassman.loggedUser.profile.id
                    ).then(function (r) {
                        uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
                    }).then(undefined, function (error) {
                        console.log(error); // TODO:
                    });
                }
            }
        }/*, function () {
            $log.info('Modal dismissed at: ' + new Date());
        }*/);
    };

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

    $scope.$watch('gassman.selectedAccount', function (accId) {
        if (accId) {
            $q.all([
                    gdata.accountMovements($scope.gassman.selectedAccount, null, 0, 5),
                    gdata.accountAmount($scope.gassman.selectedAccount)
                ])
                .then(function (rr) {
                    $scope.movements = rr[0].data.items;
                    $scope.personalAmount = rr[1].data;
                }).then(undefined, function (error) {
                $scope.loadError = error.data;
            });
        } else {
            $scope.movements = null;
            $scope.personalAmount = null;
        }
    });

    $q.when($scope.csaInfo).then(function () {
        return $q.all([
            gdata.accountAmount($scope.csa.kitty.id)
            //gdata.accountMovements($scope.csa.kitty.id, 0, 5),
        ]);
    }).
    then (function (rr) {
        $scope.csa.kitty.amount = rr[0].data;
        //$scope.csa.kitty.movements = rr[1].data;
    }).
    then (undefined, function (error) {
        if (error.data[0] != gdata.error_codes.E_permission_denied)
            $scope.loadError = error.data;
    });
}])
;