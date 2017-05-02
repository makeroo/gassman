/**
 * Created by makeroo on 27/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.AdminPerms', [
    'GassmanApp.services.Gdata',
    'ngStorage'
])

.controller('AdminPerms', [
         '$scope', '$localStorage', 'gdata', 'listController',
function ($scope,   $localStorage,   gdata,   listController) {

    var permissions = [
        [ gdata.permissions.P_canViewContacts, 'Vedere contatti' ],
        [ gdata.permissions.P_canEditContacts, 'Editare contatti' ],

        [ gdata.permissions.P_canCheckAccounts, 'Controllare conti' ],

        [ gdata.permissions.P_canManageShifts, 'Gestire turni' ],

        [ gdata.permissions.P_canEnterCashExchange, 'Inserire scambi contante' ],
        [ gdata.permissions.P_canEnterPayments, 'Inserire pagamenti' ],
        [ gdata.permissions.P_canEditMembershipFee, 'Inserire pagamenti quota' ],
        [ gdata.permissions.P_canManageTransactions, 'Controllare movimenti' ],

        [ gdata.permissions.P_canCloseAccounts, 'Chiudere conti' ],

        [ gdata.permissions.P_csaEditor, 'GAS editor' ],

        [ gdata.permissions.P_canAdminPeople, 'Amministrare account' ],
        [ gdata.permissions.P_canGrantPermissions, 'Gestire conti' ]
    ];

    $scope.grantablePermissions = [];

    angular.forEach(permissions, function (p) {
        if ($scope.gassman.loggedUser.permissions.indexOf(p[0]) !== -1) {
            $scope.grantablePermissions.push(p);
        }
    });

    $scope.selectedPermission = $scope.grantablePermissions[0];

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

                    e.hasGrant = function () {
                        return e.profile && e.profile.permissions.indexOf($scope.selectedPermission[0]) !== -1;
                    };
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

    $scope.toggleGrant = function (p, e) {
        e.stopPropagation();

        if (!p.profile) {
            return; // ci riprovo dopo, sto caricando
        }

        var grantPos = p.profile.permissions.indexOf($scope.selectedPermission[0]);

        if (grantPos !== -1) {
            gdata.revokePermission($scope.gassman.selectedCsa, p[0], $scope.selectedPermission[0]).then(function (r) {
               p.profile.permissions.splice(grantPos, 1);
            }).then (undefined, function (error) {
                console.log('casino', error); // TODO
            });
        } else {
            gdata.grantPermission($scope.gassman.selectedCsa, p[0], $scope.selectedPermission[0]).then(function (r) {
                p.profile.permissions.push($scope.selectedPermission[0]);
            }).then(undefined, function (error) {
                console.log('casino', error); // TODO
            });
        }
    };
}])
;
