/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaBase', [
    'ui.calendar',

    'GassmanApp.services.Gdata'
])

.controller('CsaBase', [
         '$scope', '$filter', '$location', '$stateParams', 'gdata', '$q', '$uibModal', 'uiCalendarConfig',
function ($scope,   $filter,   $location,   $stateParams,   gdata,   $q,   $uibModal,   uiCalendarConfig) {
    var csaId = $stateParams.csaId;

    $scope.csa = null;
    $scope.loadError = null;
    $scope.cal_info = {
        selected_event: null,
        prepare_event: function (delivery_date) {
            return delivery_date;
        }
    };

    $scope.eventSources = [
        function (start, end, timezone, callback) {
            gdata.deliveryDates($scope.gassman.selectedCsa, start.toJSON(), end.toJSON()).then(function (r) {
                var events = r.data;
                var dest = [];
                var oldSelected = $scope.cal_info.selected_event;

                $scope.cal_info.selected_event = null;

                angular.forEach(events, function (e) {
                    var now = moment().utc();

                    e.from_date = moment(e.from_time).utc();
                    e.to_date = moment(e.to_time).utc();
                    e.editable = e.from_date > now;

                    e.delivery_place = $scope.deliveryPlacesIndex[e.delivery_place_id];
                    var myShift = null;

                    angular.forEach(e.shifts, function (s, idx) {
                        if (s.person_id == $scope.gassman.loggedUser.profile.id) {
                            myShift = idx;
                        }

                        gdata.profile($scope.gassman.selectedCsa, s.person_id).then(function (r) {
                            s.person = r;
                        }).then (undefined, function (error) {
                            s.personError = error;
                        });
                    });

                    if (myShift !== null) {
                        e.myShift = e.shifts.splice(myShift, 1)[0];
                    }

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

                    if (oldSelected && oldSelected.id == e.id)
                        $scope.cal_info.selected_event = $scope.cal_info.prepare_event(e);
                });

                callback(dest);
                $scope.eventsError = null;
            }).then(undefined, function (error) {
                $scope.eventsError = error.data;
            });
        }
    ];

    $scope.editableMembershipFee = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canEditMembershipFee) != -1;
    $scope.editableCsaInfo = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_csaEditor) != -1;
    $scope.editableCsaDeliveryDates = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canManageShifts) != -1;

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

    var csaDefer = $q.defer();

    $scope.csaInfo = function () {
        return csaDefer.promise;
    };

    $q.all([
        gdata.csaInfo(csaId),
        gdata.deliveryPlaces(csaId)
    ])
    .then (function (r) {
        $scope.csa = r[0].data;
        $scope.csa.kitty.membership_fee = parseFloat($scope.csa.kitty.membership_fee);
        $scope.deliveryPlaces = r[1].data;

        csaDefer.resolve($scope.csa);

        $scope.deliveryPlaces.sort(function (a, b) {
            return a.id - b.id;
        });

        $scope.deliveryPlacesIndex = {};
        angular.forEach($scope.deliveryPlaces, function (dp, idx) {
            $scope.deliveryPlacesIndex[dp.id] = dp;

            dp.color = colors[idx % colors.length];
        });
    }).
    then (undefined, function (error) {
        if (error.data[0] != gdata.error_codes.E_permission_denied)
            $scope.loadError = error.data;
    });
}])

.controller('AddShiftPopup', [
         '$scope', '$uibModalInstance', 'event', 'shift',
function ($scope,   $uibModalInstance,   event,   shift) {
    $scope.event = event;
    $scope.shift = shift;
    $scope.role = shift ? shift.role : '';

    $scope.ok = function () {
        $uibModalInstance.close([ $scope.shift, $scope.role ]);
    };

    $scope.cancel = function () {
        $uibModalInstance.close([ $scope.shift, null ]);
        //$uibModalInstance.dismiss('cancel');
    };
}])
;
