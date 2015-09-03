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
        { p:gdata.permissions.P_canEnterCashExchange, f:'#/transaction/x', l:'Inserisci scambio contante' },
        { p:gdata.permissions.P_canEnterPayments, f:'#/transaction/p', l:'Registra pagamenti' },
        //{ p:gdata.permissions.P_canEnterDeposit, f:'#/transaction/d', l:'Registra accrediti' },
        //{ p:gdata.permissions.P_canEnterWithdrawal, f:'#/transaction/w', l:'Registra prelievi' },
        { e: function (pp) { return gdata.canEditTransactions(null, pp); }, f:'#/transactions/index', l:' Storia dei movimenti inseriti' },
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
	}).
	then (undefined, function (error) {
		if (error != gdata.E_no_csa_found)
			$scope.initError = error;
	});
}])
;
