'use strict';

angular.module('GassmanApp.services.AccountAutocompletion', [
    ])

.service('accountAutocompletion', [
function () {
	/* Restituisce una mappa: accountId -> { acc:accountId, cur:[ id, sym ], people:{}, name:'' }
	 * E people è a sua volta una mappa: personId -> { pid:PID, name:'', refs:[ '' ] }
	 */
	this.parse = function (accountNamesData) {
		var accountCurrencies = accountNamesData.accountCurrencies;
		//var accountPeople = accountNamesData.accountPeople;
		var accountPeopleAddresses = accountNamesData.accountPeopleAddresses;
//		var kitty = accountNamesData.kitty;

		var resp = {
//			kitty: accountNamesData.kitty
		};

		angular.forEach(accountCurrencies, function (o) {
			//              0     1     2         3             4                  5           6            7
			// o è un array a.id, c.id, c.symbol, ap.from_date, owner (person_id), first_name, middle_name, last_name
			// NB: un conto compare tante volte quanti sono i suoi intestatari correnti
			var account_id = o[0];
			var account_record = resp[account_id];
			var valid_from = new Date(o[3]);

			if (account_record === undefined) {
				account_record = {
					acc: account_id,
					cur: [o[1], o[2]],
					people: {},
					name: '',
					valid_from: valid_from
				};

				resp[account_id] = account_record;
			} else {
				if (valid_from < account_record.valid_from)
					account_record.valid_from = valid_from;
			}

			account_record.people[o[4]] = {
				pid: o[4],
				name: joinSkippingEmpties(' ', o[5], o[6], o[7]),
				refs: []
			}
		});
/*
		angular.forEach(accountPeople, function (o) {
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + ' ' + (o[2] || '') + ' ' + (o[3] || '');
			n = n.trim();

			var aa = resp[o[4]];
			if (aa) {
				aa.people[o[0]] = { pid:o[0], name: n, refs:[] };
			} else {
				console.log('accountAutocompletion: accountPeople record without currency info:', o);
			}
		});
*/
		angular.forEach(accountPeopleAddresses, function (o) {
			// o è un array 0:addr 1:pid 2:accId
			var aa = resp[o[2]];

			if (aa) {
				var pp = aa.people[o[1]];
				if (pp)
					pp.refs.push(o[0]);
				else
					console.log('accountAutocompletion: address without person:', o)
			} else {
				console.log('accountAutocompletion: accountPeopleAddresses record without currency info:', o);
			}
		});
/*
		for (var i in kitty) {
			var k = kitty[i];

			var aa = resp[k];

			if (aa) {
				aa.people['kitty'] = { name:'CASSA COMUNE', refs:[] }; // FIXME: i18n
			} else {
				console.log('accountAutocompletion: kitty account without currency info:', k);
			}
		}
*/
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

			if (l.name)
				resp.push(l);
		});

		return resp;
	};

	this.parse_people = function (people_names_data) {
		var accountPeople = people_names_data.people;
		var accountPeopleAddresses = people_names_data.addresses;

		var resp = { };

		angular.forEach(accountPeople, function (o) {
			// o è un array 0:pid, 1:fname, 2:mname, 3:lname, 4:accId
			var n = (o[1] || '') + (o[2] ? (' ' + o[2]) : '') + (o[3] ? (' ' + o[3]) : '');

			n = n.trim();

			resp[o[0]] = { pid:o[0], name: n, refs:[], acc:o[4] };
		});

		angular.forEach(accountPeopleAddresses, function (o) {
			// o è un array 0:addr 1:pid 2:accId
			var pp = resp[o[1]];

			if (pp) {
				pp.refs.push(o[0]);
			} else {
				console.log('accountAutocompletion: address without person:', o)
			}
		});

		return resp;
	};

	this.compose_people = function (people_index) {
		var resp = [];

		angular.forEach(people_index, function (l) {
			if (l.refs.length)
				l.search = l.name + ' (' + l.refs.join(', ') + ')';
			else
				l.search = l.name;

			if (l.search)
				resp.push(l);
		});

		return resp;
	};
}])
;
