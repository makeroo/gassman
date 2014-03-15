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

gassmanControllers.controller('AccountDetails', function($scope, $http, $filter, $routeParams, $location) {
	$scope.uiMode = 'accountLoading';
	$scope.movements = [];
	$scope.transaction = null;

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var accId = $routeParams['accountId'];
	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.transactionAccount = function (accId) {
		try {
			var p = $scope.transaction.people[accId];
			if (p)
				// p: [id, fist, middle, last, accId]
				return p[1] + (p[2] ? ' ' + p[2] : '') + ' ' + p[3];
			var n = $scope.transaction.accounts[accId];
			return n ? n : 'N/D';
		} catch (e) {
			return 'N/D';
		}
	};

	$scope.showTransaction = function (mov) {
		$http.post('/transaction/' + mov[4] + '/detail?_xsrf=' + getCookie('_xsrf')).
		success (function (data, status, headers, config) {
			data.mov = mov;
			$scope.transaction = data;
		}).
		error (function (data, status, headers, config) {
			$scope.transaction = null;
			// TODO: errore
		});
	};

	$scope.loadMore = function () {

		if (concluded) return;

		$http.post('/account/' + (accId == undefined ? '' : (accId + '/')) + 'movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')). // null, { xsrfCookieName:'_xsrf' }).
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

gassmanControllers.controller('AccountsIndex', function($scope, $http, $filter, $location) {
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

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/details');
	};

	$scope.loadMore();
});