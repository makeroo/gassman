'use strict';

var gassmanServices = angular.module('gassmanServices', [
    'ngCookies',
	'ngStorage',
    ]);

/*
 * strada non percorribile perché:
 * 1) in config non ho disponibilità di $cookies (NON so perché)
 * 2) i transformRequest ricevono solo data
 * 3) gli interceptors ricevono solo config
 *    MA CONFIG CONTIENE url:''!
gassmanServices.config(function ($httpProvider) {
	$httpProvider.defaults.transformRequest.push(function (data) {
		// TODO: qua devo aggiungere ?_xsrf=$cookies._xsrf alla query
		console.log(arguments);
		return data;
	});
});
*/

gassmanServices.service('gdata', function ($http, $q, $localStorage, $cookies) {
	var profileInfo = null;

	this.E_class = "<class 'Exception'>";
	this.E_already_modified = 'already modified';

	this.isError = function (rdata, ecode) {
		return (
			angular.isArray(rdata) &&
			rdata.length > 1 &&
			rdata[0] == this.E_class &&
			(ecode == undefined || rdata[1] == ecode)
			);
	};

	this.sysVersion = function () {
		return $http.post('/sys/version?_xsrf=' + $cookies._xsrf);
	}

	this.profileInfo = function () {
		var d = $q.defer();

		if (profileInfo) {
			d.resolve(profileInfo);
		} else {
			$http.post('/profile-info?_xsrf=' + $cookies._xsrf).
			success(function (data) {
				profileInfo = data;
				d.resolve(profileInfo);
			}).
			error(function () {
				d.reject(data);
			});
		}

		return d.promise;
	}

	this.selectedCsa = function (csaId) {
		var d = $q.defer();

		if (csaId === undefined) {
			// restituisce il csa selezionato

			this.profileInfo().then(
				function (pi) {
					var x = $localStorage.selectedCsa;

					if (x === undefined || !(x in pi.csa)) {
						for (var i in pi.csa) {
							x = i;
							break;
						}
						if (x) {
							$localStorage.selectedCsa = x;
							d.resolve(x);
						} else {
							d.reject('noCsaFound');
						}
					} else {
						d.resolve(x);
					}
				},
				function (error) {
					d.reject(error);
				}
			);
		} else {
			// imposta il csa selezionato

			this.profileInfo().then(
				function (pi) {
					if (accId in pi.csa) {
						$localStorage.selectedCsa = csaId;
						d.resolve(csaId);
					} else {
						d.reject('notMember');
					}
				},
				function (error) {
					d.reject(error);
				}
			);
		}

		return d.promise;
	}

	this.accountByCsa = function (csaId) {
		// restituisci l'account dell'utente loggato in base al csa indicato
		var d = $q.defer();

		this.profileInfo().then(
			function (pi) {
				var done = false;
				for (var i in pi.accounts) {
					// accDetails è: 0:csaId 1:accId 2:from 3:to
					var accDetails = pi.accounts[i];
					if (accDetails[0] == csaId && accDetails[3] == null) {
						d.resolve(accDetails[1]);
						done = true;
						break;
					}
				}
				
				if (!done)
					d.reject('noAccount');
			},
			function (error) {
				d.reject(error);
			}
		);

		return d.promise;
	}

	this.totalAmount = function (csaId) {
		return $http.post('/csa/' + csaId + '/total_amount?_xsrf=' + $cookies._xsrf);
	}

	this.accountsIndex = function (csaId, start, blockSize) {
		return $http.post('/accounts/' + csaId + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf);
	}

	this.accountsNames = function (csaId) {
		return $http.post('/accounts/1/names?_xsrf=' + $cookies._xsrf);
	}

	this.accountAmount = function (accId) {
		return $http.post('/account/' + accId + '/amount?_xsrf=' + $cookies._xsrf);
	}

	this.accountOwner = function (accId) {
		return $http.post('/account/' + accId + '/owner?_xsrf=' + $cookies._xsrf);
	}

	this.accountMovements = function (accId, start, blockSize) {
		return $http.post('/account/' + accId + '/movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf); // null, { xsrfCookieName:'_xsrf' })
	}

	this.transactionDetail = function (csaId, tid) {
		return $http.post('/transaction/' + csaId + '/' + tid + '/detail?_xsrf=' + $cookies._xsrf);
	}

	this.transactionForEdit = function (csaId, tid) {
		return $http.post('/transaction/' + csaId + '/' + tid + '/edit?_xsrf=' + $cookies._xsrf);
	}

	this.transactionSave = function (csaId, tData) {
		return $http.post('/transaction/' + csaId + '/save?_xsrf=' + $cookies._xsrf, tData);
	}

	this.transactionsLog = function (csaId, start, blockSize) {
		return $http.post('/transactions/' + csaId + '/editable/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf);
	}
});
