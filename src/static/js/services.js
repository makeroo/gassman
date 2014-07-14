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

gassmanServices.service('gdata', function ($http, $q, $localStorage, $cookies, $rootScope, $timeout) {
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

	this.accountsIndex = function (csaId, query, order, start, blockSize) {
		return $http.post('/accounts/' + csaId + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf, { q: query, o: order });
	}

	this.accountsNames = function (csaId) {
		return $http.post('/accounts/' + csaId + '/names?_xsrf=' + $cookies._xsrf);
	}

	this.expensesTags = function (csaId) {
		return $http.post('/expenses/' + csaId + '/tags?_xsrf=' + $cookies._xsrf);
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
		var p = $http.post('/transaction/' + csaId + '/save?_xsrf=' + $cookies._xsrf, tData);
		p.then(function (r) {
			$rootScope.$broadcast('AmountsChanged');
			return r;
		});
		return p;
	}

	this.transactionsLog = function (csaId, start, blockSize) {
		return $http.post('/transactions/' + csaId + '/editable/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf);
	}

	this.peopleIndex = function (csaId, query, order, start, blockSize) {
		return $http.post('/people/' + csaId + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies._xsrf, { q: query, o: order });
	}

	this.peopleProfiles = function (csaId, pids) {
		return $http.post('/people/' + csaId + '/profiles?_xsrf=' + $cookies._xsrf, { pids: pids });
	}

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
	}
});

gassmanServices.service('accountAutocompletion', function ($http, $q, $localStorage, $cookies, $rootScope) {
	this.parse = function (accountNamesData) {
		var accountCurrencies = accountNamesData.accountCurrencies;
		var accountPeople = accountNamesData.accountPeople;
		var accountPeopleAddresses = accountNamesData.accountPeopleAddresses;

		var resp = {};

		for (var i in accountCurrencies) {
			var o = accountCurrencies[i];
			// o è un array a.id, c.id, c.symbol
			resp[o[0]] = { acc:o[0], cur: [ o[1], o[2] ], people: {}, name:'' };
		}
		for (var i in accountPeople) {
			var o = accountPeople[i];
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + ' ' + (o[2] || '') + ' ' + (o[3] || '');
			n = n.trim();

			var aa = resp[o[4]];
			if (aa) {
				aa.people[o[0]] = { name: n, refs:[] };
			} else {
				console.log('accountPeople record without currency info:', o);
			}
		}
		for (var i in accountPeopleAddresses) {
			var o = accountPeopleAddresses[i];
			// o è un array 0:addr 1:pid 2:accId
			var aa = resp[o[2]];

			if (aa) {
				var pp = aa.people[o[1]];
				if (pp)
					pp.refs.push(o[0]);
				else
					console.log('address without person:')
			} else {
				console.log('accountPeopleAddresses record without currency info:', o);
			}
		}

		return resp;
	};

	this.compose = function (currencies) {
		var resp = [];

		angular.forEach(currencies, function (l) {
			var x = [];
			angular.forEach(l.people, function (i) {
				if (i.refs.length)
					x.push(i.name + ' (' + i.refs.join(', ') + ')');
				else
					x.push(i.name);
			});

			l.name = x.join(', ');
			//l.label = 'Intestatari: ' + l.name;
			resp.push(l);
		});

		return resp;
	};
});
