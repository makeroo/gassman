/**
 * Created by makeroo on 27/05/15.
 */

'use strict';

angular.module('GassmanApp.filters.HumanTimeDiff', [
    'GassmanApp.services.Iso8601Parser'
])

.filter('humanTimeDiff', [
         'iso8601Parser',
function (iso8601Parser) {

	var isSameDay = function (d1, d2) {
		return d1.getFullYear() == d2.getFullYear() && d1.getMonth() == d2.getMonth() && d1.getDate() == d2.getDate();
	};
/*
	var isToday = function (d) {
		return isSameDay(d, new Date());
	};
*/
	var toStartOfTheDay = function (d) {
		d.setHours(0);
		d.setMinutes(0);
		d.setSeconds(0);
		d.setMilliseconds(0);
	};

	return function (input) {
		if (!input)
			return '';

		var d = iso8601Parser.jsonStringToDate(input);
		var now = new Date();

		if (isSameDay(d, now))
			return 'oggi';

		toStartOfTheDay(now);

		var td = now - d; // td è in millisecondi

		td /= 1000 * 60 * 60; // adesso è in ore
		td /= 24; // adesso è in giorni

		if (td < 2)
			return 'ieri';

		if (td < 14)
			return parseInt(td) + ' giorni fa';

		if (td < 30)
			return parseInt(td / 7) + ' settimane fa';

		if (td < 60)
			return '1 mese fa';

		if (td < 359)
			return parseInt(td / 30) + ' mesi fa';

		if (td < 730)
			return '1 anno fa';

		return parseInt(td / 365) + ' anni fa';
	};
}])
;
