


/*
gassmanControllers.controller('MenuController', function($scope, $filter, gdata) {
	$scope.profile = null;
	$scope.profileError = null;
	$scope.functions = [];
	$scope.amount = null;
	$scope.amountError = null;
	$scope.currencySymbol = null;
	$scope.amountClass = null;
	$scope.csaId = null;
	$scope.accountId = null;

	var reloadAmounts = function () {
		gdata.accountAmount($scope.accountId).
		then (function (r) {
			$scope.amountError = null;
			$scope.amount = parseFloat( r.data[0] );
			$scope.currencySymbol = r.data[1];

			$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
		}).
		then (undefined, function (error) {
			$scope.amount = null;
			$scope.currencySymbol = null;
			$scope.amountError = error.data;
		})/ *.
		done()* /;
	};

	$scope.$on('AmountsChanged', function () {
		reloadAmounts();
	});

	gdata.profileInfo().
	then (function (pData) {
		$scope.profile = pData;

		angular.forEach(gassmanApp.functions, function (f) {
			if (('p' in f && pData.permissions.indexOf(f.p) == -1) ||
				('e' in f && !f.e(pData.permissions))
				)
				return;

			$scope.functions.push(f);
		});

		return gdata.selectedCsa();
	}).
	then (function (csaId) {
		$scope.csaId = csaId;
		return gdata.csaInfo(csaId);
	}).
	then (function (r) {
		$scope.csa = r.data;
		return gdata.accountByCsa($scope.csaId);
	}).
	then (function (accId) {
		$scope.accountId = accId;
		reloadAmounts();
	}).
	then (undefined, function (error) {
		$scope.profileError = error;
	});
});
*/




/*
gassmanControllers.controller('ContactsController', function($scope, $filter, $location, gdata) {
	$scope.people = [];
	$scope.peopleError = null;
	$scope.queryFilter = '';
	$scope.queryOrder = 0;

	var start = 0;
	var blockSize = 25;
	$scope.concluded = false;

	var lastQuery = '';
	var lastQueryOrder = 0;

	$scope.search = function () {
		if ($scope.queryFilter == lastQuery && $scope.queryOrder == lastQueryOrder)
			return;
		lastQuery = $scope.queryFilter;
		lastQueryOrder = $scope.queryOrder;

		reset();
		$scope.loadMore();
	};

	var reset = function () {
		$scope.people = [];
		$scope.peopleError = null;
		start = 0;
		$scope.concluded = false;
	};

	$scope.loadMore = function () {
		if ($scope.concluded) return;

		gdata.selectedCsa().
		then (function (csaId) { return gdata.peopleIndex(csaId, lastQuery, lastQueryOrder, start, blockSize); }).
		then(function (r) {
			$scope.concluded = r.data.length < blockSize;
			start += r.data.length;
			$scope.people = $scope.people.concat(r.data);
		}).
		then (undefined, function (error) {
			$scope.concluded = true;
			$scope.peopleError = error.data;
		});
	};

	$scope.showProfile = function (personId) {
		$location.path('/person/' + personId + '/detail');
	};

	$scope.loadMore();
});
*/
