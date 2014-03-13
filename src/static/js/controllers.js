'use strict';

var gassmanControllers = angular.module('gassmanControllers', []);

gassmanControllers.controller('MenuController', function($scope, $http, $filter) {
	$scope.functions = [];

	$http.post('/profile-info?_xsrf=' + getCookie('_xsrf')).
	success(function (data, status, headers, config) {
		$scope.profile = data;

		for (var i in data.permissions) {
			var f = gassmanApp.permissions[data.permissions[i]];
			if (f.f) {
				$scope.functions.push(f);
			}
		}
	}).
	error (function (data, status, headers, config) {
		
	});

	$http.post('/account/amount?_xsrf=' + getCookie('_xsrf')).
	success(function (data, status, headers, config) {
		$scope.amount = parseFloat( data[0] );
		$scope.currencySymbol = data[1];

		$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
//			$filter('currency')(data[0], data[1]);
	}).
	error (function (data, status, headers, config) {
		$scope.amountClass = 'error';
		//console.log('error', data, status, headers, config);
	});
});

gassmanControllers.controller('AccountDetails', function($scope, $http, $filter) {
	$scope.uiMode = 'accountLoading';
	$scope.movements = [];

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.loadMore = function () {

		if (concluded) return;

		$http.post('/account/movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')). // null, { xsrfCookieName:'_xsrf' }).
		success (function (data, status, headers, config) {
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

});

gassmanControllers.controller('AccountsIndex', function($scope, $http, $filter) {
	$scope.uiMode = 'accountsLoading';
	$scope.accounts = [];

	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.loadMore = function () {
		if (concluded) return;

		$http.post('/accounts/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')).
		success (function (data, status, headers, config) {
			concluded = data.length < blockSize;
			start += data.length;
			$scope.uiMode = 'accountsOk';
			$scope.accounts = $scope.accounts.concat(data);
		}).
		error (function (data, status, headers, config) {
			concluded = true;
			// TODO: mostrare errore
		});
	};

	$scope.loadMore();
});