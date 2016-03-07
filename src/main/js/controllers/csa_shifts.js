/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaShifts', [
    'GassmanApp.services.Gdata',
    'GassmanApp.services.AccountAutocompletion',
    'GassmanApp.directives.GmValidTime',
    'GassmanApp.directives.GmAfter'
])

.controller('CsaShifts', [
         '$scope', '$filter', '$location', '$stateParams', 'gdata', 'uiCalendarConfig', '$q', 'accountAutocompletion', '$locale',
function ($scope,   $filter,   $location,   $stateParams,   gdata,   uiCalendarConfig,   $q,   accountAutocompletion,   $locale) {
    var csaId = $stateParams.csaId;

    $scope.csa = null;
    $scope.loadError = null;

    $scope.cancel = function () {
        $location.path('/csa/' + csaId + '/detail');
    };

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
            var event = calEvent.deliveryDate;

            event.delivery_places = [
                event.delivery_place
            ];

            event.enabled_dp = {};
            event.enabled_dp[event.delivery_place.id] = true;

            event.from_hour = $filter('date')(event.from_date.toJSON(), 'shortTime');
            event.to_hour = $filter('date')(event.to_date.toJSON(), 'shortTime');

            $scope.selectedEvent = event;
        },
        dayClick: function (date, jsEvent, view) {
            var start = moment(date); //.add(18, 'hour');
            var end = moment(date); //.add(19, 'hour');

            //var hour_start = $filter('date')(start.toJSON(), 'shortTime');
            //var hour_end = $filter('date')(end.toJSON(), 'shortTime');

            var event = {
                delivery_place_id: null,
                shifts: [],
                from_time: start.toJSON(),
                to_time: end.toJSON(),
                notes: '',
                from_date: start,
                to_date: end,
                from_hour: '', //hour_start,
                to_hour: '', //hour_end,
                editable: true,
                delivery_place: null,
                delivery_places: [],
                enabled_dp: {}
            };

            angular.forEach($scope.deliveryPlaces, function (dp) {
                event.delivery_places.push(dp);
                event.enabled_dp[dp.id] = false;
            });

            $scope.selectedEvent = event;

            //console.log('day click', arguments);
        }
        //eventDrop: $scope.alertOnDrop,
        //eventResize: $scope.alertOnResize
    };

    $scope.assignedDp = function () {
        for (var l = $scope.selectedEvent.delivery_places.length; --l >= 0; ) {
            var dp = $scope.selectedEvent.delivery_places[l];

            if ($scope.selectedEvent.enabled_dp[dp.id])
                return true;
        }

        return false;
    };

    $scope.timeFormat = $locale.DATETIME_FORMATS.shortTime;

    $scope.saveEvent = function () {
        var promises = [];

        angular.forEach($scope.selectedEvent.enabled_dp, function (enabled, dpId) {
            if (!enabled)
                return;

            var start = $scope.selectedEvent.from_date;
            var end = $scope.selectedEvent.to_date;

            var hs = moment($scope.selectedEvent.from_hour, $scope.timeFormat).utc();
            var he = moment($scope.selectedEvent.to_hour, $scope.timeFormat).utc();

            start.hour(hs.hour());
            start.minutes(hs.minute());

            end.hour(he.hour());
            end.minute(he.minute());

            var event = {
                id: $scope.selectedEvent.id,
                from_time: start.toJSON(),
                to_time: end.toJSON(),
                notes: $scope.selectedEvent.notes,
                delivery_place_id: dpId,
                shifts: $scope.selectedEvent.shifts
            };

            promises.push(gdata.saveEvent($scope.gassman.selectedCsa, event));
        });

        $q.all(promises).then(function (r) {
            $scope.selectedEvent.id = r[0].data.id;

            uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
        }).then(undefined, function (error) {
            $scope.saveError = error.data;
        });
    };

    $scope.removeEvent = function () {
        gdata.removeEvent($scope.gassman.selectedCsa, $scope.selectedEvent.id).then(function (r) {
            $scope.cancelEvent();
            uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
        }).then(undefined, function (error) {
            $scope.saveError = error.data;
        });

    };

    $scope.cancelEvent = function () {
        $scope.selectedEvent = null;
    };

    $scope.addShift = function () {
        $scope.selectedEvent.shifts.push({
            role: '',
            person_id: null,
            idx: $scope.selectedEvent.shifts.length
        });
    };

    $scope.removeShift = function (idx) {
        $scope.selectedEvent.shifts.splice(idx, 1);

        angular.forEach($scope.selectedEvent.shifts, function (e, idx) {
            e.idx = idx;
        });
    };

    gdata.accountsNames($scope.gassman.selectedCsa).then(function (r) {
        $scope.currencies = accountAutocompletion.parse(r.data);
        $scope.autocompletionData = accountAutocompletion.compose($scope.currencies);
    }).then(undefined, function (error) {
        $scope.autocompletionDataError = error.data;
    });
}])
;
