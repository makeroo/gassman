'use strict';

var gassmanControllers = angular.module('gassmanControllers', []);

gassmanControllers.controller('MenuController', function($scope, $http, $filter) {
	$scope.profile = null;
	$scope.profileError = null;
	$scope.functions = [];
	$scope.totalAmount = null;
	$scope.totalAmountError = null;
	$scope.amount = null;
	$scope.amountError = null;
	$scope.currencySymbol = null;
	$scope.amountClass = null;

	$http.post('/profile-info?_xsrf=' + getCookie('_xsrf')).
	success(function (data, status, headers, config) {
		$scope.profile = data;

		for (var i in data.permissions) {
			var f = gassmanApp.permissions[data.permissions[i]];
			if (f.f) {
				$scope.functions.push(f);

				if (f.v == gassmanApp.P_canCheckAccounts) {
					$http.post('/csa/total_amount?_xsrf=' + getCookie('_xsrf')).
					success(function (data, status, headers, config) {
						$scope.totalAmount = data;
					}).
					error (function (data, status, headers, config) {
						$scope.totalAmountError = data;
					});
				}
			}
		}
	}).
	error (function (data, status, headers, config) {
		$scope.profileError = data;
	});

	$http.post('/account/amount?_xsrf=' + getCookie('_xsrf')).
	success(function (data, status, headers, config) {
		$scope.amount = parseFloat( data[0] );
		$scope.currencySymbol = data[1];

		$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
	}).
	error (function (data, status, headers, config) {
		$scope.amountError = data;
	});
});

gassmanControllers.controller('AccountDetails', function($scope, $http, $filter, $routeParams, $location) {
	$scope.movements = [];
	$scope.movementsError = null;
	$scope.transaction = null;
	$scope.transactionError = null;
	$scope.accountOwner = null;
	$scope.accountOwnerError = null;
//	$scope.selectedMovement = null;

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var accId = $routeParams['accountId'];
	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$http.post('/account/' + (accId == undefined ? 'self' : accId) + '/owner?_xsrf=' + getCookie('_xsrf')).
	success (function (data, status, headers, config) {
		$scope.accountOwner = data;
	}).
	error (function (data, status, headers, config) {
		$scope.accountOwnerError = data;
	});

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
		$scope.transaction = null;
		$scope.transactionError = null;
//		$scope.selectedMovement = mov[4];
		$http.post('/transaction/' + mov[4] + '/detail?_xsrf=' + getCookie('_xsrf')).
		success (function (data, status, headers, config) {
			data.mov = mov;
			$scope.transaction = data;
		}).
		error (function (data, status, headers, config) {
			$scope.transactionError = data;
		});
	};

	$scope.loadMore = function () {
		if (concluded) return;

		$http.post('/account/' + (accId == undefined ? '' : (accId + '/')) + 'movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')). // null, { xsrfCookieName:'_xsrf' }).
		success (function (data, status, headers, config) {
			concluded = data.length < blockSize;
			start += data.length;
			$scope.movements = $scope.movements.concat(data);
		}).
		error (function (data, status, headers, config) {
			concluded = true;
			$scope.serverError = data[1];
			console.log('movements error:', data)
			$scope.showErrorMessage = false;
			$scope.movementsError = data;
			//console.log('error', data, status, headers, config);
		});
	};

	$scope.loadMore();

});

gassmanControllers.controller('AccountsIndex', function($scope, $http, $filter, $location) {
	$scope.accounts = [];
	$scope.accountsError = null;

	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.loadMore = function () {
		if (concluded) return;

		$http.post('/accounts/index/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')).
		success (function (data, status, headers, config) {
			concluded = data.length < blockSize;
			start += data.length;
			$scope.accounts = $scope.accounts.concat(data);
		}).
		error (function (data, status, headers, config) {
			concluded = true;
			$scope.accountsError = data;
		});
	};

	$scope.showAccount = function (accountId) {
		$location.path('/account/' + accountId + '/details');
	};

	$scope.loadMore();
});

gassmanControllers.controller('HelpController', function() {
});

gassmanControllers.controller('FaqController', function() {
});

gassmanControllers.controller('ProjectController', function($scope, $http) {
	$scope.version = null;

	$http.post('/sys/version?_xsrf=' + getCookie('_xsrf')).
	success (function (data, status, headers, config) {
		$scope.version = data[0];
	}); // non gestisco l'errore
});
