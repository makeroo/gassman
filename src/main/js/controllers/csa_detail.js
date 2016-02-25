/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaDetail', [
    'ui.calendar',

    'GassmanApp.services.Gdata'
])

.controller('CsaDetail', [
         '$scope', '$filter', '$location', '$stateParams', 'gdata', '$q',
function ($scope,   $filter,   $location,   $stateParams,   gdata,   $q) {
    var csaId = $stateParams.csaId;

    $scope.csa = null;
    $scope.loadError = null;
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
            right: 'today prev,next'
        },
        titleFormat: '[Turni] MMMM YYYY',
        eventClick: function (calEvent, jqueryEvent) {
            $scope.selectedEvent = calEvent.deliveryDate;
        }
        //dayClick: $scope.alertEventOnClick,
        //eventDrop: $scope.alertOnDrop,
        //eventResize: $scope.alertOnResize
    };

    $scope.eventSources = [
        function (start, end, timezone, callback) {
            gdata.deliveryDates($scope.gassman.selectedCsa, start.toJSON(), end.toJSON()).then(function (r) {
                var events = r.data;
                var dest = [];

                angular.forEach(events, function (e) {
                    e.from_date = moment(e.delivery_date).utc();
                    e.to_date = moment(start);

                    e.from_date.add(e.from_time, 's');
                    e.to_date.add(e.to_time, 's');

                    e.delivery_place = $scope.deliveryPlacesIndex[e.delivery_place_id];

                    angular.forEach(e.shifts, function (s) {
                        gdata.profile($scope.gassman.selectedCsa, s.person_id).then(function (r) {
                            s.person = r;
                        }).then (undefined, function (error) {
                            s.personError = error;
                        });
                    });

                    dest.push({
                        id: e.id,
                        title: e.notes,
//                        allDay: false,
                        start: e.from_date.toJSON(),
                        end: e.to_date.toJSON(),
//                        editable: false,
                        color: e.delivery_place.color,
                        deliveryDate: e
                    });
                });

                callback(dest);
                $scope.eventsError = null;
            }).then(undefined, function (error) {
                $scope.eventsError = error.data;
            });
        }
    ];

    $scope.editCsa = function () {
        $location.path('/csa/' + csaId + '/admin');
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

    $scope.editableMembershipFee = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;
    $scope.editableCsaInfo = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_csaEditor) != -1;

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

    var colors = [
        'palevioletred',
        'lightsalmon',
        'limegreen',
        'lemonchiffon',
        'lavender',
        'paletorquoise',
        'cornsilk',
        'skyblue',

        'pink',
        'coral',
        'palegreen',
        'papayawhip',
        'thistle',
        'cadetblue',
        'tan',
        'cornflowerblue',

        'mediumvioletred',
        'darkorange',
        'olivedrab',
        'mocassin',
        'plum',
        'lightsteelblue',
        'sandybrown',
        'lightblue'
    ];

    $q.all([
        gdata.csaInfo(csaId),
        gdata.deliveryPlaces(csaId)
    ])
    .then (function (r) {
        $scope.csa = r[0].data;
        $scope.csa.kitty.membership_fee = parseFloat($scope.csa.kitty.membership_fee);
        $scope.deliveryPlaces = r[1].data;

        $scope.deliveryPlaces.sort(function (a, b) {
            return a.id - b.id;
        });

        $scope.deliveryPlacesIndex = {};
        angular.forEach($scope.deliveryPlaces, function (dp, idx) {
            $scope.deliveryPlacesIndex[dp.id] = dp;

            dp.color = colors[idx % colors.length];
        });

        // TODO: in realtà degli ordini CPY mi interessano solo le mie ordinazioni!!
        return $q.all([
            gdata.accountAmount($scope.csa.kitty.id),
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
