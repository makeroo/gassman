/**
 * Created by makeroo on 16/04/15.
 */

'use strict';

angular.module('GassmanApp.controllers.Navbar', [ 'gassmanServices' ])

.controller('NavbarController', [
         '$scope', 'gdata', '$q',
function ($scope,   gdata,   $q) {
    var ttypes = [
        { p:gassmanApp.P_canEnterCashExchange, f:'#/transaction/x', l:'Inserisci scambio contante' },
        { p:gassmanApp.P_canEnterPayments, f:'#/transaction/p', l:'Registra pagamenti' },
        { p:gassmanApp.P_canEnterDeposit, f:'#/transaction/d', l:'Registra accrediti' },
        { p:gassmanApp.P_canEnterWithdrawal, f:'#/transaction/w', l:'Registra prelievi' },
        { e: function (pp) { return gassmanApp.canEditTransactions(null, pp); }, f:'#/transactions/index', l:' Storia dei movimenti inseriti' },
        ];
/*        //{ p:gassmanApp.P_membership, f:'#/account/detail', l:'Il tuo conto' },
        { e:function (pp) {
            return pp.indexOf(gassmanApp.P_canCheckAccounts) != -1 ||
                   pp.indexOf(gassmanApp.P_canViewContacts) != -1;
            }, f:'#/accounts/index', l:'Membri del G.A.S.' },
        //{ v:P_canAssignAccounts, f:null },
        { e: function (pp) { return gassmanApp.canEditTransactions(null, pp) }, l:'Movimentazione contante', 'class': "grouptitle" },
        ];
*/
	$scope.transactionTypes = [];

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;
		$scope.csaId = null;
    	$scope.initError = null;

		angular.forEach(ttypes, function (f) {
			if (('p' in f && pData.permissions.indexOf(f.p) == -1) ||
				('e' in f && !f.e(pData.permissions))
				)
				return;

			$scope.transactionTypes.push(f);
		});

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;
		return $q.all([ gdata.csaInfo(csaId),
		                gdata.accountByCsa(csaId)
		                ]);
	}).
	then (function (r) {
		$scope.csa = r[0].data;
		$scope.accId = r[1];
        console.log('resp3 ', r)
	}).
	then (undefined, function (error) {
		$scope.initError = error;
	});
}])
;