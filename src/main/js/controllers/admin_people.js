/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AdminPeople', [
    'GassmanApp.services.Gdata',
    'ngStorage'
])

.controller('AdminPeople', [
         '$scope', '$localStorage', 'gdata', 'listController',
function ($scope,   $localStorage,   gdata,   listController) {

    function subscope (scope, prop, o) {
        o = o || {};

        scope[prop] = o;

        o.$watch = function (k, f) {
            scope.$watch(prop + '.' + k, f);
        };

        return o;
    }

    $scope.others = {};

    listController.setupScope(
        subscope($scope, 'others'),
        // data service
        function (from, pageSize, filterBy) {
            return gdata.adminPeopleIndex(
                filterBy.q,
                filterBy.csa,
                filterBy.o,
                from,
                pageSize
            );
        },
        // options
        {
            // pageLoadedHook: function () { },
            filterBy: {
                q: '',
                csa: null,
                o: '1'
            },

            pageSizes: [ 5, 10, 20 ],
            storage: $localStorage,
            storageKey: 'admin_people'
        }
    );
}])
;
