/**
 * Created by makeroo on 26/05/15.
 */

'use strict';

angular.module('GassmanApp.services.Gdata', [
    'ngCookies',
	'ngStorage'
    ])

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

.service('gdata', [
         '$http', '$q', '$localStorage', '$cookies', '$rootScope', '$timeout',
function ($http,   $q,   $localStorage,   $cookies,   $rootScope,   $timeout) {
	var gdata = this;
	var profileInfo = null;
	var peopleProfiles = {};

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
			error(function (data) {
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
	};

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
	};

	this.csaInfo = function (csaId) {
		return $http.post('/csa/' + csaId + '/info?_xsrf=' + $cookies._xsrf);
	};

	this.chargeMembershipFee = function (csaId, p) {
		return $http.post('/csa/' + csaId + '/charge_membership_fee?_xsrf=' + $cookies._xsrf, p);
	};

	this.accountsIndex = function (csaId, query, order, start, blockSize) {
		return $http.post('/accounts/' + csaId + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf, { q: query, o: order });
	};

	this.accountsNames = function (csaId) {
		return $http.post('/accounts/' + csaId + '/names?_xsrf=' + $cookies._xsrf);
	};

	this.expensesTags = function (csaId) {
		return $http.post('/expenses/' + csaId + '/tags?_xsrf=' + $cookies._xsrf);
	};

	this.accountAmount = function (accId) {
		return $http.post('/account/' + accId + '/amount?_xsrf=' + $cookies._xsrf);
	};

	this.accountOwner = function (accId) {
		return $http.post('/account/' + accId + '/owner?_xsrf=' + $cookies._xsrf);
	};

	this.accountMovements = function (accId, start, blockSize) {
		return $http.post('/account/' + accId + '/movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf); // null, { xsrfCookieName:'_xsrf' })
	};

	this.transactionForEdit = function (csaId, tid) {
		return $http.post('/transaction/' + csaId + '/' + tid + '/edit?_xsrf=' + $cookies._xsrf);
	};

	this.transactionSave = function (csaId, tData) {
		var p = $http.post('/transaction/' + csaId + '/save?_xsrf=' + $cookies._xsrf, tData);
		p.then(function (r) {
			$rootScope.$broadcast('AmountsChanged');
			return r;
		});
		return p;
	};

	this.transactionsLog = function (csaId, query, order, start, blockSize) {
		return $http.post('/transactions/' + csaId + '/editable/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf, { q: query, o: order });
	};

	this.peopleIndex = function (csaId, query, order, start, blockSize) {
		return $http.post('/people/' + csaId + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf, { q: query, o: order });
	};

	this.peopleProfiles = function (csaId, pids) {
		return $http.post('/people/' + csaId + '/profiles?_xsrf=' + $cookies._xsrf, { pids: pids });
	};

	var PROFILE_REQUEST_DELAY = .300; // secondi
	var profilesToRequest = {};
	var profilesRequestTimeout = null;

	var keysOf = function (o) {
		if (o === undefined || o === null || angular.isArray(o))
			return o;
		if (!angular.isObject(o))
			return [];
		var r = [];
		for (var p in o)
			if (o.hasOwnProperty(p))
				r.push(p);
		return r;
	}

	var instrumentProfile = function (p) {
		angular.forEach(p.contacts, function (c) {
			if (c.kind == 'E') {
				if (!p.mainEmail)
					p.mainEmail = c.address;
			} else if (c.kind == 'T') {
				if (!p.mainTelephone)
					p.mainTelephone = c.address;
			}
		});
	};

	this.profile = function (csaId, pid) {
		var d = $q.defer();

		if (pid in peopleProfiles) {
			d.resolve(peopleProfiles[pid])
		} else {
			var defers = profilesToRequest[pid];

			if (!defers) {
				defers = [];
				profilesToRequest[pid] = defers;
			}

			defers.push(d);

			if (profilesRequestTimeout === null) {
				profilesRequestTimeout = $timeout(function () {
					profilesRequestTimeout = null;

					var ptr = profilesToRequest;

					profilesToRequest = {};

					// ptr.keys() mi lancia un'eccezione che non ho capito
					var pids = keysOf(ptr);

					gdata.peopleProfiles(csaId, pids).
					then(function (r) {
						angular.forEach(r.data, function (e) {
							var pid = e.profile.id;

							instrumentProfile(e);

							peopleProfiles[pid] = e;

							var defers = ptr[pid];

							angular.forEach(defers, function (d) {
								d.resolve(e);
							});
						});
					}).
					then(undefined, function (error) {
						d.reject(error.data);
					});
				}, PROFILE_REQUEST_DELAY);
			}
		}

		return d.promise;
	};

	this.saveProfile = function (csaId, p) {
		return $http.post('/person/' + csaId + '/save?_xsrf=' + $cookies._xsrf, p);
	};

	this.uniqueEmail = function (csaId, pid, email) {
		return $http.post('/person/' + csaId + '/check_email?_xsrf=' + $cookies._xsrf, {
			'id': pid,
			'email': email
		});
	};
}])
;
