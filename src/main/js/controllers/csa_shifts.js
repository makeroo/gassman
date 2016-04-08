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

    $scope.cal_info.prepare_event = function (delivery_date) {
        var event = delivery_date;

        event.delivery_places = [
            event.delivery_place
        ];

        event.enabled_dp = {};
        event.enabled_dp[event.delivery_place.id] = true;

        event.from_hour = $filter('date')(event.from_date.toJSON(), 'shortTime');
        event.to_hour = $filter('date')(event.to_date.toJSON(), 'shortTime');

        return event;
    };

    $scope.calendar = {
        //height: 450,
        editable: false,
        header:{
            left: 'title', //month basicWeek basicDay agendaWeek agendaDay',
            //center: '',
            right: 'prev,next' // today
        },
        titleFormat: '[Turni] MMMM YYYY',
        eventRender: function(event, element) {
            if ($scope.cal_info.selected_event && event.id == $scope.cal_info.selected_event.id) {
                element.addClass('selected');
            }
            if (event.deliveryDate.shifts.length > 0) {
                element.addClass('covered');
            } else {
                element.addClass('uncovered');
            }
            //console.log('rendering event', event, element);
        },
        eventClick: function (calEvent, jqueryEvent) {
            $scope.cal_info.selected_event = $scope.cal_info.prepare_event(calEvent.deliveryDate);
            uiCalendarConfig.calendars.uical.fullCalendar('rerenderEvents');
        },
        dayClick: function (date, jsEvent, view) {
            var start = moment(date).utc(); //.add(18, 'hour');
            var end = moment(date).utc(); //.add(19, 'hour');

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

            $scope.cal_info.selected_event = event;

            //console.log('day click', arguments);
        }
        //eventDrop: $scope.alertOnDrop,
        //eventResize: $scope.alertOnResize
    };

    $scope.assignedDp = function () {
        for (var l = $scope.cal_info.selected_event.delivery_places.length; --l >= 0; ) {
            var dp = $scope.cal_info.selected_event.delivery_places[l];

            if ($scope.cal_info.selected_event.enabled_dp[dp.id])
                return true;
        }

        return false;
    };

    $scope.timeFormat = $locale.DATETIME_FORMATS.shortTime;

    $scope.saveEvent = function () {
        var promises = [];

        angular.forEach($scope.cal_info.selected_event.enabled_dp, function (enabled, dpId) {
            if (!enabled)
                return;

            var start = $scope.cal_info.selected_event.from_date;
            var end = $scope.cal_info.selected_event.to_date;

            // fullcalendar me le riporta local...
            start.utc();
            end.utc();

            var hs = moment($scope.cal_info.selected_event.from_hour, $scope.timeFormat).utc();
            var he = moment($scope.cal_info.selected_event.to_hour, $scope.timeFormat).utc();

            start.hour(hs.hour());
            start.minutes(hs.minute());

            end.hour(he.hour());
            end.minute(he.minute());

            var event = {
                id: $scope.cal_info.selected_event.id,
                from_time: start.toJSON(),
                to_time: end.toJSON(),
                notes: $scope.cal_info.selected_event.notes,
                delivery_place_id: dpId,
                shifts: $scope.cal_info.selected_event.shifts
            };

            promises.push(gdata.saveEvent($scope.gassman.selectedCsa, event));
        });

        $q.all(promises).then(function (r) {
            $scope.cal_info.selected_event.id = r[0].data.id;

            uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
        }).then(undefined, function (error) {
            $scope.saveError = error.data;
        });
    };

    $scope.removeEvent = function () {
        gdata.removeEvent($scope.gassman.selectedCsa, $scope.cal_info.selected_event.id).then(function (r) {
            $scope.cancelEvent();
            uiCalendarConfig.calendars.uical.fullCalendar('refetchEvents');
        }).then(undefined, function (error) {
            $scope.saveError = error.data;
        });

    };

    $scope.cancelEvent = function () {
        $scope.cal_info.selected_event = null;
    };

    $scope.addShift = function () {
        $scope.cal_info.selected_event.shifts.push({
            role: '',
            person_id: null,
            idx: $scope.cal_info.selected_event.shifts.length
        });
    };

    $scope.removeShift = function (idx) {
        $scope.cal_info.selected_event.shifts.splice(idx, 1);

        angular.forEach($scope.cal_info.selected_event.shifts, function (e, idx) {
            e.idx = idx;
        });
    };

    gdata.people_names($scope.gassman.selectedCsa).then(function (r) {
        $scope.peoples = accountAutocompletion.parse_people(r.data);
        $scope.autocompletionData = accountAutocompletion.compose_people($scope.peoples);
    }).then(undefined, function (error) {
        $scope.autocompletionDataError = error.data;
    });
}])
;
