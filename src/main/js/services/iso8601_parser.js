/**
 * Created by makeroo on 27/05/15.
 */

/**
 * Created by makeroo on 27/05/15.
 */

'use strict';

angular.module('GassmanApp.services.Iso8601Parser', [

])

.service('iso8601Parser', [

function () {
	this.jsonStringToDate = function (string) {
		var R_ISO8601_STR = /^(\d{4})-?(\d\d)-?(\d\d)(?:T(\d\d)(?::?(\d\d)(?::?(\d\d)(?:\.(\d+))?)?)?(Z|([+-])(\d\d):?(\d\d))?)?$/;
		// 1        2       3         4          5          6          7          8  9     10      11
		var int = parseInt;
		var match;

		if (match = string.match(R_ISO8601_STR)) {
			var date = new Date(0),
				tzHour = 0,
				tzMin = 0,
				dateSetter = match[8] ? date.setUTCFullYear : date.setFullYear,
				timeSetter = match[8] ? date.setUTCHours : date.setHours;

			if (match[9]) {
				tzHour = int(match[9] + match[10]);
				tzMin = int(match[9] + match[11]);
			}
			dateSetter.call(date, int(match[1]), int(match[2]) - 1, int(match[3]));

			var h = int(match[4] || 0) - tzHour;
			var m = int(match[5] || 0) - tzMin;
			var s = int(match[6] || 0);
			var ms = Math.round(parseFloat('0.' + (match[7] || 0)) * 1000);

			timeSetter.call(date, h, m, s, ms);

			return date;
		}

		return string;
	};
}])

;
