/**
 * Created by makeroo on 27/05/15.
 */

'use strict';

angular.module('GassmanApp.filters.AlphaTimeDiff', [
    'GassmanApp.services.Iso8601Parser'
])

.filter('alphaTimeDiff', [
         'iso8601Parser',
function (iso8601Parser) {
	return function (input) {
		if (!input)
			return '1.0'; // sulla fiducia
		var d = iso8601Parser.jsonStringToDate(input);
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
}])
;
