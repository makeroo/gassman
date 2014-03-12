'use strict';

function getCookie (name) {
	var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return r ? r[1] : undefined;
}

/* Controllers */

var gassmanApp = angular.module('gassmanApp', [
	'ngRoute',
	'gassmanControllers'
	]);
/*
gassmanApp.filter('noFractionCurrency',
		  [ '$filter', '$locale',
		  function(filter, locale) {
			var currencyFilter = filter('currency');
			var formats = locale.NUMBER_FORMATS;
			return function(amount, currencySymbol) {
			  var value = currencyFilter(amount, currencySymbol);
			  var sep = value.indexOf(formats.DECIMAL_SEP);
			  if(amount >= 0) { 
				return value.substring(0, sep);
			  }
			  return value.substring(0, sep) + ')';
			};
		  } ]);
*/

gassmanApp.config([ '$routeProvider',
	function ($routeProvider) {
		$routeProvider.
			when('/account-details', {
				templateUrl: 'static/partials/account-details.html',
				controller: 'AccountDetails'
			}).
			when('/accounts-index', {
				templateUrl: 'static/partials/accounts-index.html',
				controller: 'AccountsIndex'
			}).
			otherwise({
				redirectTo: '/account-details'
			})
	}]);

gassmanApp.directive('whenScrolled', function() {
	return function (scope, elm, attr) {
		var raw = elm[0];

		elm.bind('scroll', function() {
			if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
				scope.$apply(attr.whenScrolled);
			}
		});
	};
});
