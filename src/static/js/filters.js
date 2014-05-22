var gassmanFilters = angular.module('gassmanFilters', []);

gassmanFilters.R_ISO8601_STR = /^(\d{4})-?(\d\d)-?(\d\d)(?:T(\d\d)(?::?(\d\d)(?::?(\d\d)(?:\.(\d+))?)?)?(Z|([+-])(\d\d):?(\d\d))?)?$/;
                               // 1        2       3         4          5          6          7          8  9     10      11

gassmanFilters.jsonStringToDate = function (string) {
	var int = parseInt;
	var match;

	if (match = string.match(gassmanFilters.R_ISO8601_STR)) {
		var date = new Date(0),
			tzHour = 0,
			tzMin  = 0,
			dateSetter = match[8] ? date.setUTCFullYear : date.setFullYear,
			timeSetter = match[8] ? date.setUTCHours : date.setHours;

		if (match[9]) {
			tzHour = int(match[9] + match[10]);
			tzMin = int(match[9] + match[11]);
		}
		dateSetter.call(date, int(match[1]), int(match[2]) - 1, int(match[3]));

		var h = int(match[4]||0) - tzHour;
		var m = int(match[5]||0) - tzMin;
		var s = int(match[6]||0);
		var ms = Math.round(parseFloat('0.' + (match[7]||0)) * 1000);

		timeSetter.call(date, h, m, s, ms);

		return date;
	}

	return string;
}

gassmanFilters.filter('humanTimeDiff', function () {

	return function (input) {
		if (!input)
			return '';

		var d = gassmanFilters.jsonStringToDate(input);

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
});

gassmanFilters.filter('alphaTimeDiff', function () {
	return function (input) {
		if (!input)
			return '1.0'; // sulla fiducia
		var d = gassmanFilters.jsonStringToDate(input);
		var td = new Date() - d;
		var op = 1.0;
		var f = 7;

		for (var c = 86400000 * 7; op > .3; c *= f) {
			if (td < c)
				break;

			op -= .1;
			f -= 1.4;
		}

		return '' + op;
	}
});
