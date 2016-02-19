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

    listController.setupScope(
        [ $scope, 'others' ],
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
            pageLoadedHook: function () {
                angular.forEach($scope.others.items, function (e) {
                    if (e.profile)
                        return;
                    var pid = e[0];
                    gdata.adminProfile(pid).
                    then(function (p) {
                        e.profile = p;
                    });
                });
            },
            filterBy: {
                q: '',
                csa: null,
                o: '1'
            },

            pageSizes: [ 5, 10, 20 ],
            storage: $localStorage,
            storageKey: 'admin_people_others'
        }
    );

    listController.setupScope(
        [ $scope, 'members' ],
        // data service
        function (from, pageSize, filterBy) {
            return gdata.accountsIndex(
                filterBy.csa,
                filterBy,
                from,
                pageSize
            );
        },
        // options
        {
            pageLoadedHook: function () {
                angular.forEach($scope.members.items, function (e) {
                    if (e.profile)
                        return;
                    var pid = e[0];
                    gdata.profile($scope.members.filterBy.csa, pid).
                    then(function (p) {
                        e.profile = p;
                    });
                });
            },
            filterBy: {
                q: '',
                csa: $scope.gassman.selectedCsa,
                o: '1',
                dp: '-1',
                ex: false
            },
            pageSizes: [ 5, 10, 20 ],
            storage: $localStorage,
            storageKey: 'admin_people_members'
        }
    );

    $scope.$watch('others.pagination.filterBy.q', function (v) {
        $scope.members.pagination.filterBy.q = v;
    });

    $scope.$watch('members.pagination.pageSize', function (v) {
        $scope.others.pagination.pageSize = v;
    });
}])
;
