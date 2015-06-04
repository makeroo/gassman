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
		var accountPeople = accountNamesData.accountPeople;
		var accountPeopleAddresses = accountNamesData.accountPeopleAddresses;
		var kitty = accountNamesData.kitty;

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
				aa.people[o[0]] = { pid:o[0], name: n, refs:[] };
			} else {
				console.log('accountAutocompletion: accountPeople record without currency info:', o);
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
					console.log('accountAutocompletion: address without person:', o)
			} else {
				console.log('accountAutocompletion: accountPeopleAddresses record without currency info:', o);
			}
		}
		for (var i in kitty) {
			var k = kitty[i];

			var aa = resp[k];

			if (aa) {
				aa.people['kitty'] = { name:'CASSA COMUNE', refs:[] }; // FIXME: i18n
			} else {
				console.log('accountAutocompletion: kitty account without currency info:', k);
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

			if (l.name)
				resp.push(l);
		});

		return resp;
	};
}])
;
