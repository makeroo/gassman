/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaBase', [
    'ui.calendar',

    'GassmanApp.services.Gdata'
])

.controller('CsaBase', [
         '$scope', '$filter', '$location', '$transition$', 'gdata', '$q', '$uibModal', 'uiCalendarConfig',
function ($scope,   $filter,   $location,   $transition$,   gdata,   $q,   $uibModal,   uiCalendarConfig) {
    var csaId = $transition$.params().csaId;

    $scope.loadError = null;
    $scope.cal_info = {
        selected_event: null,
        prepare_event: function (delivery_date) {
            return delivery_date;
        },
        dp_filter: {}
    };

    $scope.eventSources = [
        function (start, end, timezone, callback) {
            gdata.deliveryDates($scope.gassman.selectedCsa, start.toJSON(), end.toJSON(), $scope.cal_info.dp_filter).then(function (r) {
                var events = r.data.delivery_dates;
                var profiles = r.data.profiles;
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

                        if (s.person = profiles[s.person_id]) {
                            gdata.instrumentProfile(s.person);
                        }
                    });

                    if (myShift !== null) {
                        e.myShift = e.shifts.splice(myShift, 1)[0];
                    }

                    dest.push({
                        id: e.id,
                        title: e.notes,
//                        allDay: false,
                        start: moment(e.from_date.local()),
                        end: moment(e.to_date.local()),
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
        'tan',
        'lightsalmon',
        'skyblue',
        'cornflowerblue',
        'lavender',
        'palevioletred',

        'pink',
        'palegreen',
        'papayawhip',
        'thistle',
        'cadetblue',
        'olivedrab',

        'darkorange',
        'mocassin',
        'plum',
        'lightsteelblue',
        'sandybrown',
        'lightblue'
    ];

    $scope.toggle_dp_filter = function (dp) {
        $scope.cal_info.dp_filter[dp.id] = !$scope.cal_info.dp_filter[dp.id];

        uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
    };

    gdata.deliveryPlaces(csaId).then (function (r) {
        $scope.deliveryPlaces = r.data;

        angular.forEach($scope.deliveryPlaces, function (dp) {
            $scope.cal_info.dp_filter[dp.id] = true;
        });

        $scope.deliveryPlaces.sort(function (a, b) {
            return a.id - b.id;
        });

        $scope.deliveryPlacesIndex = {};
        angular.forEach($scope.deliveryPlaces, function (dp, idx) {
            $scope.deliveryPlacesIndex[dp.id] = dp;

            dp.color = colors[idx % colors.length];
        });
    }).then (undefined, function (error) {
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
