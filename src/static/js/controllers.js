'use strict';

/* Controllers */

var gassmanApp = angular.module('gassmanApp', []);
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
gassmanApp.controller('AccountDetail', function($scope, $http, $filter) {
	$scope.uiMode = 'accountLoading';

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	$http.get('/account/movements/0/5').
		success(function (data, status, headers, config) {
			$scope.uiMode = 'accountOk';
			$scope.movements = data;
		}).
		error (function (data, status, headers, config) {
			$scope.serverError = data[1];
			console.log('movements error:', data)
			$scope.showErrorMessage = false;
			$scope.uiMode = 'accountFailed';
			//console.log('error', data, status, headers, config);
		});

	$http.get('/account/amount').
		success(function (data, status, headers, config) {
			$scope.amount = $filter('currency')(data[0], data[1]);
			//console.log($scope.amount, data, status, headers, config);
		}).
		error (function (data, status, headers, config) {
			//console.log('error', data, status, headers, config);
		});
});
