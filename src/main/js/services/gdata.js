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
         '$http', '$q', '$cookies', '$rootScope', '$timeout',
function ($http,   $q,   $cookies,   $rootScope,   $timeout) {
    var gdata = this;
    var peopleProfiles = {};

    this.permissions = {
        //P_membership: 1,
        P_canCheckAccounts: 2,
        P_canAdminPeople: 3,
        //P_canEnterDeposit: 4,
        P_canEnterPayments: 5,
        P_canManageTransactions: 6,
        P_canEnterCashExchange: 7,
        //P_canEnterWithdrawal: 8,
        P_canViewContacts: 9,
        P_canEditContacts: 10,
        P_canEditMembershipFee: 12,
        P_csaEditor: 13,
        P_canCloseAccounts: 14,
        P_canManageShifts: 15
    };

    this.gadgets = {
        piggyBank: 'piggy-bank',
        debt: 'exclamation-sign'
    };

    this.E_class = "<class 'Exception'>";

    this.error_codes = {
        // locali
        E_no_csa_found: 'no csa found', // non è presente alcun csa nel local storage
        E_person_not_found: 'person not found', // personId non trovato, generato localmente perché il server in questo caso restituisce lista vuota
        E_no_account:  'no account', // una persona non ha il conto per un dato csa

        // server
        E_ok: '',
        E_not_authenticated:  'not authenticated', // restituito quando si assume che ci sia già qualcuno autenticato ma non è così. TODO: gestire che in questo caso si salta alla login
        E_illegal_payload:  'illegal payload', // richiesta ajax con payload non valido (non gestito, bug del client)
        E_permission_denied:  'permission denied', // richiesta operazione non permessa (non gestito, bug del client)
        E_already_modified:  'already modified', // # transaction.id, quando si salva una transazione ma qualcuno l'ha già modificata (TODO: gestire)
        E_type_mismatch:  'type mismatch', // in modifica transazione il nuovo tipo non è compatibile col precedente (non gestito, bug del client)
        E_no_lines:  'no lines', // si tenta di salvare una transazione senza righe (non gestito, bug del client)
        E_illegal_currency:  'illegal currency', // il csa non gestisce la moneta indicata (non gestito, bug del client)
        E_illegal_delete:  'illegal delete', // si è tentato di cancellare una transazione non cancellabile (non gestito, bug del client)
        E_trashed_transactions_can_not_have_lines:  'trashed transactions can not have lines', // ditto (non gestito, bug del client)
        E_missing_trashId_of_transaction_to_be_deleted:  'missing trashId of transaction to be deleted', // ditto (non gestito, bug del client)
        E_illegal_transaction_type:  'illegal transaction type', // si tenta di salvare una transazione con tipo sconosciuto (non gestito, bug del client)
        //E_illegal_receiver:  'illegal receiver',
        E_accounts_do_not_belong_to_csa:  'accounts do not belong to csa', // le linee di una transazione riferiscono account appartenenti a csa diversi da quello della transazione (non gestito, bug del client)
        E_accounts_not_omogeneous_for_currency_and_or_csa:  'accounts not omogeneous for currency and/or csa', // le linee di una transazione riferiscono account appartenenti a più di un csa o associati a monete diverse fra loro (non gestito, bug del client)
        E_already_member:  'already member', // inviata richiesta di adesione da parte di un membro già appartenente al csa TODO: gestire
        I_account_open:  'account open', // a seguito di una richiesta di chiusura conto si notifica che il conto appartiene anche ad altre persone e quindi rimane aperto (per le altre)
        E_not_owner_or_already_closed:  'not owner or already closed', // a seguito di una richiesta di chiusura conto, il conto era già chiuso oppure la persona indicata non era owner (gestito implicitamente)
        I_empty_account:  'empty account', // a seguito di una richiesta di chiusura conto si notifica che il conto era vuoto e quindi non è stato necessario inserire una transazione 'z' di chiusura
        E_illegal_amount: 'illegl amount', // ammontare negativo nelle transazioni (non gestito, bug del client)
        E_illegal_kitty: 'illegal kitty' // kitty account id non risolto (non gestito, bug del client)
    };

    this.isError = function (rdata, ecode) {
        return (
            angular.isArray(rdata) &&
            rdata.length > 1 &&
            rdata[0] == gdata.E_class &&
            (ecode == undefined || rdata[1] == ecode)
            );
    };

    this.isPk = function (v) {
        try {
            var i = parseInt(v);

            return !isNaN(i);
        } catch (e) {
            return false;
        }
    };

    var transactionTypes = {
        d: true, // non editabile gdata.permissions.P_canEnterDeposit,
        // e, errore, solo backend
        f: gdata.permissions.P_canEditMembershipFee,
        g: true, // non editabile
        p: gdata.permissions.P_canEnterPayments,
        q: true, // non editabile gdata.permissions.P_canEnterPayments
        // r TODO
        t: true, // vale il tipo della precedente
        // u, unfinished, solo backend
        w: true, // non editabile gdata.permissions.P_canEnterWithdrawal,
        x: gdata.permissions.P_canEnterCashExchange,
        z: gdata.permissions.P_canCloseAccounts
    };

    this.isValidTransactionType = function (v) {
        return !!transactionTypes[v];
    };

    this.isTransactionTypeEditableByUser = function (t, u) {
        var p = transactionTypes[t];

        if (angular.isNumber(p))
            return u.permissions.indexOf(p) != -1;
        else
            return false;
    };

    this.canEditTransactions = function (u) {
        if (!u)
            return false;

        var pp = u.permissions || [];

        return (
            pp.indexOf(gdata.permissions.P_canEnterPayments) != -1 ||
            pp.indexOf(gdata.permissions.P_canEnterCashExchange) != -1 ||
            pp.indexOf(gdata.permissions.P_canEditMembershipFee) != -1 ||
            pp.indexOf(gdata.permissions.P_canManageTransactions) != -1
            );
    };

    this.sysVersion = function () {
        return $http.post('/gm/sys/version?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.profileInfo = function (csa_id) {
        //return $http.post('/gm/profile-info?_xsrf=' + $cookies.get('_xsrf'));
        return $http.post('/gm/people/' + csa_id + '/profiles?_xsrf=' + $cookies.get('_xsrf'), { pids: ['me'] }).then(function (r) {
            var p = null;
            angular.forEach(r.data, function (o) {
                p = o;
                gdata.instrumentProfile(p);
            });
            r.data = p;
            return r;
        });
    };

    this.accountByCsa = function (csa_id) {
        // restituisci l'account dell'utente loggato in base al csa indicato

        var pi = $rootScope.gassman.loggedUser;

        if (pi) {
            var lastAccount = null;

            for (var i = 0; i < pi.accounts.length; ++i) {
                // accDetails è: 0:csa_id 1:accId 2:from 3:to
                var accDetails = pi.accounts[i];

                if (accDetails.csa_id == csa_id && accDetails.to_date == null) {
                    return accDetails.id;
                }

                if (lastAccount == null || lastAccount.to_date < accDetails.to_date) {
                    lastAccount = accDetails;
                }
            }

            return lastAccount == null ? null : lastAccount.id;
        } else {
            throw gdata.error_codes.E_not_authenticated;
        }
    };

    this.csaInfo = function (csa_id) {
        return $http.post('/gm/csa/' + csa_id + '/info?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.csaList = function () {
        return $http.post('/gm/csa/list?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.csaUpdate = function (csa) {
        return $http.post('/gm/csa/update?_xsrf=' + $cookies.get('_xsrf'), csa);
    };

    this.deliveryPlaces = function (csa_id) {
        return $http.post('/gm/csa/' + csa_id + '/delivery_places?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.deliveryDates = function (csa_id, from, to, selected_dp) {
        return $http.post('/gm/csa/' + csa_id + '/delivery_dates?_xsrf=' + $cookies.get('_xsrf'),
            {
                from: from,
                to: to,
                delivery_places: selected_dp
            });
    };

    this.addShift = function (csa_id, eventId, shiftId, role, userId) {
        return $http.post('/gm/csa/' + csa_id + '/add_shift?_xsrf=' + $cookies.get('_xsrf'), {
            delivery_date_id: eventId,
            person_id: userId,
            role: role,
            id: shiftId
        });
    };

    this.removeShift = function (csa_id, shiftId) {
        return $http.post('/gm/csa/' + csa_id + '/remove_shift?_xsrf=' + $cookies.get('_xsrf'), {
            id: shiftId
        });
    };

    this.chargeMembershipFee = function (csa_id, p) {
        return $http.post('/gm/csa/' + csa_id + '/charge_membership_fee?_xsrf=' + $cookies.get('_xsrf'), p);
    };

    this.setMembershipFee = function (csa_id, person_id, fee) {
        return $http.post('/gm/person/' + csa_id + '/set_fee?_xsrf=' + $cookies.get('_xsrf'), {
            pid: person_id,
            fee: fee
        });
    };

    this.accountsIndex = function (csa_id, query, start, blockSize) {
        return $http.post(
            '/gm/accounts/' + csa_id + '/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies.get('_xsrf'),
            query
        );
    };

    this.accountsNames = function (csa_id) {
        return $http.post('/gm/accounts/' + csa_id + '/names?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.accountAmount = function (accId) {
        return $http.post('/gm/account/' + accId + '/amount?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.accountOwner = function (accId) {
        return $http.post('/gm/account/' + accId + '/owner?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.accountMovements = function (accId, filterBy, start, blockSize) {
        return $http.post('/gm/account/' + accId + '/movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies.get('_xsrf'), {
            filter: filterBy
        });
    };

    this.transactionForEdit = function (csa_id, tid, fetchKitty) {
        return $http.post('/gm/transaction/' + csa_id + '/' + tid + '/edit?_xsrf=' + $cookies.get('_xsrf'), {
            fetchKitty: fetchKitty
        });
    };

    this.transactionSave = function (csa_id, tData) {
        return $http.post('/gm/transaction/' + csa_id + '/save?_xsrf=' + $cookies.get('_xsrf'), tData);
    };

    this.transactionsLog = function (csa_id, query, order, start, blockSize) {
        return $http.post('/gm/transactions/' + csa_id + '/editable/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies.get('_xsrf'), { q: query, o: order });
    };

    this.people_names = function (csa_id) {
        return $http.post('/gm/people/' + csa_id + '/names?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.peopleProfiles = function (csa_id, pids) {
        return $http.post('/gm/people/' + csa_id + '/profiles?_xsrf=' + $cookies.get('_xsrf'), { pids: pids });
    };

    this.adminPeopleProfiles = function (pids) {
        return $http.post('/gm/admin/people/profiles?_xsrf=' + $cookies.get('_xsrf'), { pids: pids });
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
    };

    this.instrumentProfile = function (p) {
        angular.forEach(p.contacts, function (c) {
            if (c.kind == 'E') {
                if (!p.mainEmail)
                    p.mainEmail = c.address;
            } else if (c.kind == 'T') {
                if (!p.mainTelephone)
                    p.mainTelephone = c.address;
            } else if (c.kind == 'M') {
                if (!p.mainMobile)
                    p.mainMobile = c.address;
            } else if (c.kind == 'P') {
                if (!p.picture)
                    p.picture = c.address;
            }
        });

        if (p.mainMobile)
            p.mainTelephone = p.mainMobile;

        p.gadgets = [];
        if (!p.permissions) {
            p.permissions = [];
        } else if (p.permissions.indexOf(gdata.permissions.P_canEnterCashExchange) != -1) {
            p.gadgets.push(gdata.gadgets.piggyBank);
        }
    };

    this.profile = function (csa_id, pid) {
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

                    gdata.peopleProfiles(csa_id, pids).
                    then(function (r) {
                        var foundPids = {};

                        angular.forEach(r.data, function (e) {
                            var pid = e.profile.id;

                            foundPids[pid] = true;

                            gdata.instrumentProfile(e);

                            peopleProfiles[pid] = e;

                            var defers = ptr[pid];

                            angular.forEach(defers, function (d) {
                                d.resolve(e);
                            });
                        });

                        angular.forEach(pids, function (p) {
                            if (foundPids.hasOwnProperty(p))
                                return;

                            var defers = ptr[p];

                            angular.forEach(defers, function (d) {
                                d.reject([ gdata.error_codes.E_person_not_found ]);
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

    var adminPeopleProfiles = {};
    var adminProfilesToRequest = {};
    var adminProfilesRequestTimeout = null;

    this.adminProfile = function (pid) {
        var d = $q.defer();

        if (pid in adminPeopleProfiles) {
            d.resolve(adminPeopleProfiles[pid])
        } else {
            var defers = adminProfilesToRequest[pid];

            if (!defers) {
                defers = [];
                adminProfilesToRequest[pid] = defers;
            }

            defers.push(d);

            if (adminProfilesRequestTimeout === null) {
                adminProfilesRequestTimeout = $timeout(function () {
                    adminProfilesRequestTimeout = null;

                    var ptr = adminProfilesToRequest;

                    adminProfilesToRequest = {};

                    // ptr.keys() mi lancia un'eccezione che non ho capito
                    var pids = keysOf(ptr);

                    gdata.adminPeopleProfiles(pids).
                    then(function (r) {
                        var foundPids = {};

                        angular.forEach(r.data, function (e) {
                            var pid = e.profile.id;

                            foundPids[pid] = true;

                            gdata.instrumentProfile(e);

                            adminPeopleProfiles[pid] = e;

                            var defers = ptr[pid];

                            angular.forEach(defers, function (d) {
                                d.resolve(e);
                            });
                        });

                        angular.forEach(pids, function (p) {
                            if (foundPids.hasOwnProperty(p))
                                return;

                            var defers = ptr[p];

                            angular.forEach(defers, function (d) {
                                d.reject([ gdata.error_codes.E_person_not_found ]);
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

    this.saveProfile = function (csa_id, p) {
        delete peopleProfiles[p.id];
        return $http.post('/gm/person/' + csa_id + '/save?_xsrf=' + $cookies.get('_xsrf'), p);
    };

    this.uniqueEmail = function (csa_id, pid, email) {
        return $http.post('/gm/person/' + csa_id + '/check_email?_xsrf=' + $cookies.get('_xsrf'), {
            'id': pid,
            'email': email
        });
    };

    this.requestMembership = function (csa_id) {
        return $http.post('/gm/csa/' + csa_id + '/request_membership?_xsrf=' + $cookies.get('_xsrf'));
    };

    this.closeAccount = function (accId, ownerId, reason) {
        delete peopleProfiles[ownerId];
        return $http.post('/gm/account/' + accId + '/close?_xsrf=' + $cookies.get('_xsrf'), { owner: ownerId, tdesc: reason });
    };

    this.adminPeopleIndex = function (query, csa, order, start, blockSize) {
		return $http.post(
            '/gm/admin/people/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + $cookies.get('_xsrf'),
            {
                q: query,
                o: order,
                csa: csa
                //vck: [ Ck_... ]
            }
        );
	};

    this.removePerson = function (pid) {
		return $http.post(
            '/gm/admin/people/remove?_xsrf=' + $cookies.get('_xsrf'),
            {
                pid: pid
            }
        );
    };

    this.joinPerson = function (newpid, oldpid) {
		return $http.post(
            '/gm/admin/people/join?_xsrf=' + $cookies.get('_xsrf'),
            {
                newpid: newpid,
                oldpid: oldpid
            }
        );
    };

    this.addMemberWithExistingAccount = function (csaid, newpid, memberid) {
		return $http.post(
            '/gm/admin/people/add?_xsrf=' + $cookies.get('_xsrf'),
            {
                csa: csaid,
                pid: newpid,
                mid: memberid
            }
        );
    };

    this.addMemberWithNewAccount = function (newpid, csa) {
		return $http.post(
            '/gm/admin/people/create_account?_xsrf=' + $cookies.get('_xsrf'),
            {
                pid: newpid,
                csa: csa
            }
        );
    };

    this.createPerson = function (q) {
		return $http.post('/gm/admin/people/create?_xsrf=' + $cookies.get('_xsrf'), q);
    };

    this.saveEvent = function (csa_id, e) {
		return $http.post('/gm/event/' + csa_id + '/save?_xsrf=' + $cookies.get('_xsrf'), e);
    };

    this.removeEvent = function (csa_id, eventId) {
		return $http.post('/gm/event/' + csa_id + '/remove?_xsrf=' + $cookies.get('_xsrf'), { id: eventId });
    };
}])
;
