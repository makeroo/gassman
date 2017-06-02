/**
 * Created by makeroo on 16/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.Navbar', [
    'GassmanApp.services.Gdata'
])

.controller('NavbarController', [
         '$scope', 'gdata', '$q',
function ($scope,   gdata,   $q) {
    var ttypes = [
        { p:gdata.permissions.P_canEnterCashExchange, f:'root.transaction_detail', fparams:{ transId: 'x' }, l:'Inserisci scambio contante' },
        { p:gdata.permissions.P_canEnterPayments, f:'root.transaction_detail', fparams:{ transId: 'p' }, l:'Registra pagamenti' },
        //{ p:gdata.permissions.P_canEnterDeposit, f:'#/transaction/d', l:'Registra accrediti' },
        //{ p:gdata.permissions.P_canEnterWithdrawal, f:'#/transaction/w', l:'Registra prelievi' },
        { e: function (u) { return gdata.canEditTransactions(u); }, f:'root.transaction_list', fparams: null, l:' Storia dei movimenti inseriti' }
    ];
/*        //{ p:gdata.permissions.P_membership, f:'#/account/detail', l:'Il tuo conto' },
        { e:function (pp) {
            return pp.indexOf(gdata.permissions.P_canCheckAccounts) != -1 ||
                   pp.indexOf(gdata.permissions.P_canViewContacts) != -1;
            }, f:'#/accounts/index', l:'Membri del G.A.S.' },
        //{ v:P_canAssignAccounts, f:null },
        { e: function (pp) { return gdata.canEditTransactions(null, pp) }, l:'Movimentazione contante', 'class': "grouptitle" },
        ];
*/
    var otypes = [
        { f:'root.orders.list', fparams:{ type:'open' }, l:'Ordini in corso' },
        { p:gdata.permissions.P_canPlaceOrders, f:'root.orders.detail', fparams:{ orderId:'new' }, l:'Apri ordine' },
        { p:gdata.permissions.P_canPlaceOrders, f:'root.orders.list', fparams:{ type:'draft' }, l:'Ordini da aprire' },
        { p:gdata.permissions.P_canPlaceOrders, f:'root.orders.list', fparams:{ type:'closed' }, l:'Ordini in consegna' },
        { p:gdata.permissions.P_canPlaceOrders, f:'root.orders.list', fparams:{ type:'archivied' }, l:'Archivio ordini'}
    ];

    var atypes = [
        { p:gdata.permissions.P_canAdminPeople, f:'root.admin.people', l:'Utenti' },
        { p:gdata.permissions.P_canGrantPermissions, f:'root.admin.perms', l:'Permessi' }
    ];

    $scope.$watch('gassman.loggedUser', function (pData) {
        //$scope.profile = pData;
        //$scope.csaId = null;

        $scope.transactionTypes = [];
        $scope.orderTypes = [];
        $scope.adminLinks = [];

        angular.forEach(ttypes, function (f) {
            if (('p' in f && (!pData || pData.permissions.indexOf(f.p) === -1)) ||
                ('e' in f && !f.e(pData))
                )
                return;

            $scope.transactionTypes.push(f);
        });

        angular.forEach(otypes, function (f) {
            if (('p' in f && (!pData || pData.permissions.indexOf(f.p) === -1)) ||
                ('e' in f && !f.e(pData))
                )
                return;

            $scope.orderTypes.push(f);
        });

        angular.forEach(atypes, function (f) {
            if (('p' in f && (!pData || pData.permissions.indexOf(f.p) === -1)) ||
                ('e' in f && !f.e(pData))
                )
                return;

            $scope.adminLinks.push(f);
        });

        $scope.membersVisible = (
            pData && pData.permissions && (
                pData.permissions.indexOf(gdata.permissions.P_canCheckAccounts) !== -1 ||
                pData.permissions.indexOf(gdata.permissions.P_canViewContacts) !== -1
            )
        );
    });
/*
    $scope.$watch('gassman.selectedCsa', function (csaId) {
        $scope.initError = null;
        //$scope.csaId = csaId;

        if (csaId === null) {
            $scope.csa = null;
        } else {
            gdata.csaInfo(csaId)
            .then (function (r) {
                $scope.csa = r.data;
            }).
            then (undefined, function (error) {
                if (error[0] != gdata.error_codes.E_no_csa_found)
                    $scope.initError = error;
            });
        }
    });
    */
}])
;
