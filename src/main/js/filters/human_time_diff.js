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

	return function (input) {
		if (!input)
			return '';

		var d = iso8601Parser.jsonStringToDate(input);

		// provo coi giorni

		if (d.isToday())
			return 'oggi'

		var n = Date.today().addDays(-1);

		if (d.isSameDay(n))
			return 'ieri';

		for (var c = 2; c < 6; ++c) {
			n.addDays(-1);
			if (d.isSameDay(n))
				return c + ' giorni fa'
		}

		// provo con le settimane

		var td = new Date() - d; // td è in millisecondi

		td /= 1000 * 60 * 60; // adesso è in ore

		var tdweeks = parseInt(td / 24 / 7); // adesso è in settimane

		if (tdweeks == 1)
			return '1 settimana fa';
		if (tdweeks < 4)
			return tdweeks + ' settimane fa';

		var tdmonths = parseInt(td / 24 / 30); // adesso è approssimativamente in mesi

		if (tdmonths == 1)
			return '1 mese fa';
		if (tdmonths < 10)
			return tdmonths + ' mesi fa'

		var tdyears = parseInt(td / 24 / 365); // adesso è approssimativamente in anni

		if (tdyears == 1)
			return '1 anno fa'

		return tdyears + ' anni fa'
	}
}])
;
