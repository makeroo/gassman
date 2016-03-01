/**
 * Created by makeroo on 20/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.CsaShifts', [
    'GassmanApp.services.Gdata'
])

.controller('CsaShifts', [
         '$scope', '$filter', '$location', '$stateParams', 'gdata', '$q',
function ($scope,   $filter,   $location,   $stateParams,   gdata,   $q) {
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
            $scope.selectedEvent = calEvent.deliveryDate;
        },
        dayClick: function (date, jsEvent, view) {
            console.log('day click', arguments);
        }
        //eventDrop: $scope.alertOnDrop,
        //eventResize: $scope.alertOnResize
    };
}])
;
