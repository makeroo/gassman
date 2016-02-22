/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AdminPeople', [
    'GassmanApp.services.Gdata',
    'ngStorage'
])

.controller('AdminPeople', [
         '$scope', '$localStorage', 'gdata', 'listController', '$location',
function ($scope,   $localStorage,   gdata,   listController,   $location) {

    $scope.selectedPerson = null;
    $scope.selectedMember = null;

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
                    gdata.profile($scope.members.pagination.filterBy.csa, pid).
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

    $scope.pagination = {
        query: $scope.others.pagination.filterBy.q,
        pageSize: $scope.others.pagination.pageSize
    };

    $scope.$watch('pagination.query', function (v) {
        $scope.others.pagination.filterBy.q = v;
        $scope.members.pagination.filterBy.q = v;
    });

    $scope.$watch('pagination.pageSize', function (v) {
        $scope.others.pagination.pageSize = v;
        $scope.members.pagination.pageSize = v;
    });

    $scope.selectPerson = function (p) {
        if (angular.equals(p, $scope.selectedPerson)) {
            $scope.selectedPerson = null;
        } else {
            $scope.selectedPerson = p;
        }

        console.log('person selected:', $scope.selectedPerson);
    };

    $scope.selectMember = function (p) {
        $scope.selectedAccount = null;

        if (angular.equals(p, $scope.selectedMember)) {
            $scope.selectedMember = null;
        } else {
            $scope.selectedMember = p;

            if (p) {
                angular.forEach(p.profile.accounts, function (a) {
                    if (a.to_date == null) {
                        $scope.selectedAccount = a;
                    }
                });
            }
        }

        console.log('member selected:', $scope.selectedMember);
    };

    $scope.removeSelectedPerson = function () {
        gdata.removePerson($scope.selectedPerson[0]).then(function (r) {
            $scope.selectedPerson = null;

            $scope.others.loadPage(1);
        }).then (undefined, function (error) {
            $scope.actionError = error;
        });
    };

    $scope.joinPerson = function () {
        var newpid = $scope.selectedPerson[0];
        var oldpid = $scope.selectedMember[0];

        gdata.joinPerson(newpid, oldpid).then(function (r) {
            $location.path('/person/' + newpid + '/detail');
        }).then (undefined, function (error) {
            $scope.actionError = error;
        });
    };

    $scope.addMemberWithExistingAccount = function () {
        var newpid = $scope.selectedPerson[0];

        gdata.addMemberWithExistingAccount(newpid, $scope.selectedAccount.id).then(function (r) {
            $location.path('/person/' + newpid + '/detail');
        }).then (undefined, function (error) {
            $scope.actionError = error;
        });
    };

    $scope.addMemberWithNewAccount = function () {
        var newpid = $scope.selectedPerson[0];

        gdata.addMemberWithNewAccount(newpid, $scope.members.pagination.filterBy.csa).then(function (r) {
            $location.path('/person/' + newpid + '/detail');
        }).then (undefined, function (error) {
            $scope.actionError = error;
        });
    };

    $scope.addPerson = function () {
        $scope.newMember = {
            first_name: '',
            last_name: '',
            csa: true
        };
    };

    $scope.cancelAddMode = function () {
        $scope.newMember = null;
    };

    $scope.createPerson = function () {
        var account = $scope.newMember.csa;

        if (account) {
            $scope.newMember.csa = $scope.members.pagination.filterBy.csa;
        }

        gdata.createPerson($scope.newMember).then(function (r) {
            if (account) {
                var newpid = r.data.pid;

                $location.path('/person/' + newpid + '/detail');
            } else {
                $scope.newMember = null;
                $scope.others.loadPage(1);
            }
        }).then(undefined, function (error) {
            this.actionError = error;
        });
    };
}])
;
