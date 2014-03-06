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

gassmanApp.controller('AccountDetail', function($scope, $http, $filter) {
	$scope.uiMode = 'accountLoading';
	$scope.movements = [];

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var start = 0;
	var blockSize = 15;
	var concluded = false;

	$scope.loadMore = function () {
		
		if (concluded) return;

		$http.get('/account/movements/' + start + '/' + (start + blockSize)).
		success(function (data, status, headers, config) {
			concluded = data.length < blockSize;
			start += data.length;
			$scope.uiMode = 'accountOk';
			$scope.movements = $scope.movements.concat(data);
		}).
		error (function (data, status, headers, config) {
			concluded = true;
			$scope.serverError = data[1];
			console.log('movements error:', data)
			$scope.showErrorMessage = false;
			$scope.uiMode = 'accountFailed';
			//console.log('error', data, status, headers, config);
		});
	};

	$scope.loadMore();

	$http.get('/account/amount').
		success(function (data, status, headers, config) {
			$scope.amount = $filter('currency')(data[0], data[1]);
			//console.log($scope.amount, data, status, headers, config);
		}).
		error (function (data, status, headers, config) {
			//console.log('error', data, status, headers, config);
		});
});
